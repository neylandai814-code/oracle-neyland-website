"""
Oracle Live Site — build script (v2: with Map / Pro Forma / Manual Search tabs).

Scans /Users/neylandai/Documents/Oracle Reports/ for date subfolders containing
ORACLE_Dashboard_YYYY-MM-DD.html, copies each into website/runs/YYYY-MM-DD/index.html,
parses parcel_ledger.csv to build per-parcel JSON for the new tabs, then emits a
top-level website/index.html with four tabs:

  Dashboard      - sidebar of run dates + iframe panel showing the selected dashboard
  Parcel Map     - Leaflet map with city-centroid pins; today/all-time toggle
  Pro Forma      - editable assumptions on any of today's parcels; live scenario recalc
  Manual Search  - market dropdown + deep links into LoopNet/Crexi/LandWatch/etc.

Usage:
    python3 build_site.py                                 # uses default reports root
    python3 build_site.py /path/to/Oracle\ Reports        # custom root
"""

from __future__ import annotations
import os, re, sys, csv, json, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from markets import MARKETS, STATE_CENTROIDS, GROUPS, find_market, fallback_state
from index_template import INDEX_TEMPLATE

DEFAULT_REPORTS_ROOT = Path("/Users/neylandai/Documents/Oracle Reports")
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


# ============================================================================
# Discover and copy dashboards
# ============================================================================
def find_runs(reports_root: Path):
    runs = []
    for child in sorted(reports_root.iterdir(), reverse=True):
        if not child.is_dir():
            continue
        m = DATE_RE.match(child.name)
        if not m:
            continue
        dash = child / f"ORACLE_Dashboard_{child.name}.html"
        if dash.exists():
            runs.append((child.name, dash))
    return runs


def copy_dashboards(runs, site_root: Path):
    runs_dir = site_root / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    for date_str, src in runs:
        dest_dir = runs_dir / date_str
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest_dir / "index.html")
        print(f"  copied {src.name} -> runs/{date_str}/index.html")


# ============================================================================
# Parcel ledger parsing
# ============================================================================
def parse_ledger(reports_root: Path):
    """Read _oracle_brain/parcel_ledger.csv, return list of parcel dicts."""
    ledger_path = reports_root / "_oracle_brain" / "parcel_ledger.csv"
    if not ledger_path.exists():
        print(f"  WARN: no ledger at {ledger_path}; map/proforma will be empty")
        return []

    parcels = []
    with open(ledger_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            market = row.get("Market", "").strip()
            mk = find_market(market)
            if mk:
                ll = mk["ll"]
                state = mk["state"]
                market_canonical = mk["name"]
            else:
                state = fallback_state(market) or ""
                ll = STATE_CENTROIDS.get(state, [33.5, -84.0])  # Atlanta-ish fallback
                market_canonical = market

            parcels.append({
                "date": row.get("Date_First_Seen", "").strip(),
                "updated": row.get("Last_Updated", "").strip(),
                "status": row.get("Status", "").strip(),
                "source": row.get("Source_Report", "").strip(),
                "rank": row.get("Rank", "").strip(),
                "score": _to_int(row.get("Score")),
                "market_raw": market,
                "market": market_canonical,
                "state": state,
                "lat": ll[0],
                "lng": ll[1],
                "locator": row.get("Locator", "").strip(),
                "acres": row.get("Acres", "").strip(),
                "zoning": row.get("Zoning", "").strip(),
                "url": row.get("Listing_URL", "").strip(),
                "price": row.get("Asking_Price", "").strip(),
                "friction": _to_int(row.get("Friction")),
                "notes": row.get("Notes", "").strip(),
            })
    return parcels


def _to_int(v):
    try:
        return int(v) if v not in (None, "", "TBV") else None
    except (TypeError, ValueError):
        return None


def split_today_vs_history(parcels, latest_date):
    """Today's parcels = those whose source ends with _<latest_date> (e.g. 'daily_2026-05-06')."""
    today = []
    history = []
    for p in parcels:
        if p["date"] == latest_date or latest_date in (p.get("source") or ""):
            today.append(p)
        else:
            history.append(p)
    return today, history


# ============================================================================
# Market intel parsing — extract per-market observations from market_intel.md
# ============================================================================
def parse_market_intel(reports_root: Path):
    """
    Parse _oracle_brain/market_intel.md and return {canonical_market_name: [obs...]}.
    Each obs is {'date': 'YYYY-MM-DD', 'header': original ###, 'lines': [bullet text]}.
    """
    path = reports_root / "_oracle_brain" / "market_intel.md"
    if not path.exists():
        return {}

    intel = {}  # market_name -> list of observation blocks
    current_date = None
    current_market = None
    current_lines = []

    def flush():
        nonlocal current_market, current_lines
        if current_market and current_lines:
            mk = find_market(current_market)
            if mk:
                intel.setdefault(mk["name"], []).append({
                    "date": current_date or "(undated)",
                    "header": current_market,
                    "lines": list(current_lines),
                })
        current_market = None
        current_lines = []

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            # Run-date section header
            m = re.match(r"^## (\d{4}-\d{2}-\d{2})", line)
            if m:
                flush()
                current_date = m.group(1)
                continue
            # Market section header
            m = re.match(r"^### (.+?)\s*$", line)
            if m:
                flush()
                current_market = m.group(1)
                continue
            # Bullet or prose line under current market
            if current_market:
                # Skip empty lines and section dividers
                if not line.strip() or line.strip().startswith("---") or line.strip().startswith("<!--"):
                    continue
                current_lines.append(line.strip())
        flush()

    return intel


# ============================================================================
# Per-parcel pro forma defaults — derived from market + parcel
# ============================================================================
# Tier the markets by Class A new-construction blended rent ($/mo) and exit cap
# These are the same calibration ranges used by Oracle's static pro formas.
MARKET_DEFAULTS = {
    # Tier 1 (primary, strong demand)
    "Charleston, SC":             {"rent": 2200, "cap": 0.0550, "hard": 200000, "ins": 1500, "tax": 4000, "tier": "T1"},
    "Wilmington, NC":             {"rent": 2050, "cap": 0.0575, "hard": 195000, "ins": 1700, "tax": 3000, "tier": "T1"},
    "Greenville-Spartanburg, SC": {"rent": 1850, "cap": 0.0575, "hard": 190000, "ins": 1100, "tax": 2200, "tier": "T1"},
    "Greenville, SC":             {"rent": 1850, "cap": 0.0575, "hard": 190000, "ins": 1100, "tax": 2200, "tier": "T1"},
    # Tier 2
    "Knoxville, TN":              {"rent": 1800, "cap": 0.0575, "hard": 190000, "ins": 1000, "tax": 2400, "tier": "T2"},
    "Chattanooga, TN":            {"rent": 1750, "cap": 0.0600, "hard": 185000, "ins": 1100, "tax": 2400, "tier": "T2"},
    "Asheville, NC":              {"rent": 1900, "cap": 0.0600, "hard": 195000, "ins": 1100, "tax": 2400, "tier": "T2"},
    "Savannah, GA":               {"rent": 1950, "cap": 0.0575, "hard": 190000, "ins": 1500, "tax": 2200, "tier": "T2"},
    "Augusta, GA":                {"rent": 1700, "cap": 0.0600, "hard": 185000, "ins": 1300, "tax": 2200, "tier": "T2"},
    "Columbia, SC":               {"rent": 1700, "cap": 0.0600, "hard": 185000, "ins": 1100, "tax": 2200, "tier": "T2"},
    "Lakeland, FL":               {"rent": 1925, "cap": 0.0575, "hard": 195000, "ins": 1500, "tax": 4000, "tier": "T2"},
    "Ocala, FL":                  {"rent": 1750, "cap": 0.0600, "hard": 190000, "ins": 1500, "tax": 4000, "tier": "T2"},
    "Daytona Beach, FL":          {"rent": 1900, "cap": 0.0575, "hard": 195000, "ins": 1700, "tax": 4000, "tier": "T2"},
    "Tallahassee, FL":            {"rent": 1700, "cap": 0.0600, "hard": 188000, "ins": 1400, "tax": 4000, "tier": "T2"},
    "Pensacola, FL":              {"rent": 1750, "cap": 0.0625, "hard": 190000, "ins": 2200, "tax": 4000, "tier": "T2"},
    "Gainesville, FL":            {"rent": 1700, "cap": 0.0600, "hard": 188000, "ins": 1500, "tax": 4000, "tier": "T2"},
    "Lexington-Fayette, KY":      {"rent": 1750, "cap": 0.0575, "hard": 188000, "ins": 900,  "tax": 2200, "tier": "T2"},
    "Bowling Green, KY":          {"rent": 1500, "cap": 0.0625, "hard": 180000, "ins": 800,  "tax": 1800, "tier": "T2"},
    # Tier 3 / Hidden Gems
    "Tupelo, MS":                 {"rent": 1575, "cap": 0.0675, "hard": 180000, "ins": 1100, "tax": 1800, "tier": "T3"},
    "Hattiesburg, MS":            {"rent": 1450, "cap": 0.0675, "hard": 178000, "ins": 1100, "tax": 1800, "tier": "T3"},
    "Oxford, MS":                 {"rent": 1700, "cap": 0.0650, "hard": 185000, "ins": 1100, "tax": 1800, "tier": "T3"},
    "Auburn-Opelika, AL":         {"rent": 1700, "cap": 0.0625, "hard": 185000, "ins": 1100, "tax": 1500, "tier": "T3"},
    "The Shoals (Florence-Muscle Shoals), AL": {"rent": 1450, "cap": 0.0700, "hard": 175000, "ins": 1100, "tax": 1500, "tier": "T3"},
    "Cullman, AL":                {"rent": 1400, "cap": 0.0700, "hard": 175000, "ins": 1100, "tax": 1500, "tier": "T3"},
    "Dothan, AL":                 {"rent": 1475, "cap": 0.0700, "hard": 175000, "ins": 1200, "tax": 1500, "tier": "T3"},
    "Statesboro, GA":             {"rent": 1575, "cap": 0.0650, "hard": 180000, "ins": 1200, "tax": 1800, "tier": "T3"},
    "Brunswick, GA":              {"rent": 1700, "cap": 0.0675, "hard": 188000, "ins": 2000, "tax": 1800, "tier": "T3"},
    "Valdosta, GA":               {"rent": 1475, "cap": 0.0675, "hard": 180000, "ins": 1200, "tax": 1800, "tier": "T3"},
    "Aiken, SC":                  {"rent": 1500, "cap": 0.0650, "hard": 180000, "ins": 1100, "tax": 1800, "tier": "T3"},
    "Sumter, SC":                 {"rent": 1450, "cap": 0.0700, "hard": 178000, "ins": 1100, "tax": 1800, "tier": "T3"},
    "Florence, SC":               {"rent": 1575, "cap": 0.0675, "hard": 180000, "ins": 1100, "tax": 1800, "tier": "T3"},
    "Hickory, NC":                {"rent": 1500, "cap": 0.0650, "hard": 180000, "ins": 1000, "tax": 2200, "tier": "T3"},
    "Greenville, NC":             {"rent": 1500, "cap": 0.0650, "hard": 180000, "ins": 1100, "tax": 2200, "tier": "T3"},
    "Boone, NC":                  {"rent": 1700, "cap": 0.0650, "hard": 195000, "ins": 1100, "tax": 2200, "tier": "T3"},
    "Crestview / Niceville / Fort Walton Beach, FL": {"rent": 1975, "cap": 0.0625, "hard": 195000, "ins": 2200, "tax": 4000, "tier": "T3"},
    "Panama City, FL":            {"rent": 1900, "cap": 0.0650, "hard": 195000, "ins": 2400, "tax": 4000, "tier": "T3"},
    "Lake City, FL":              {"rent": 1500, "cap": 0.0700, "hard": 180000, "ins": 1500, "tax": 4000, "tier": "T3"},
    "Elizabethtown / Glendale, KY": {"rent": 1500, "cap": 0.0675, "hard": 180000, "ins": 900, "tax": 1800, "tier": "T3"},
    "Owensboro, KY":              {"rent": 1450, "cap": 0.0700, "hard": 178000, "ins": 900,  "tax": 1800, "tier": "T3"},
    "Paducah, KY":                {"rent": 1400, "cap": 0.0700, "hard": 175000, "ins": 900,  "tax": 1800, "tier": "T3"},
    "Richmond / Berea, KY":       {"rent": 1500, "cap": 0.0675, "hard": 180000, "ins": 900,  "tax": 1800, "tier": "T3"},
    "Murray, KY":                 {"rent": 1400, "cap": 0.0700, "hard": 175000, "ins": 900,  "tax": 1800, "tier": "T3"},
    # Out-of-focus but in-whitelist
    "Bryan County, GA":           {"rent": 2050, "cap": 0.0575, "hard": 195000, "ins": 1500, "tax": 2200, "tier": "T2"},
    "Pooler, GA":                 {"rent": 2050, "cap": 0.0575, "hard": 195000, "ins": 1500, "tax": 2200, "tier": "T2"},
    "Port Wentworth, GA":         {"rent": 1950, "cap": 0.0575, "hard": 195000, "ins": 1700, "tax": 2200, "tier": "T2"},
    "Jacksonville, FL":           {"rent": 1900, "cap": 0.0575, "hard": 195000, "ins": 2000, "tax": 4000, "tier": "T2"},
    "Trussville, AL":             {"rent": 1700, "cap": 0.0625, "hard": 185000, "ins": 1100, "tax": 1500, "tier": "T2"},
    "Decatur, AL":                {"rent": 1500, "cap": 0.0650, "hard": 180000, "ins": 1100, "tax": 1500, "tier": "T2"},
    "Tuscaloosa, AL":             {"rent": 1700, "cap": 0.0625, "hard": 185000, "ins": 1100, "tax": 1500, "tier": "T2"},
    "Birmingham, AL":             {"rent": 1750, "cap": 0.0600, "hard": 188000, "ins": 1100, "tax": 1500, "tier": "T2"},
    "Murfreesboro, TN":           {"rent": 1850, "cap": 0.0575, "hard": 190000, "ins": 1000, "tax": 2400, "tier": "T2"},
    "Huntsville-Madison, AL":     {"rent": 1650, "cap": 0.0625, "hard": 185000, "ins": 1100, "tax": 1500, "tier": "T2"},
    "Conway / Myrtle Beach, SC":  {"rent": 1850, "cap": 0.0625, "hard": 195000, "ins": 1900, "tax": 1500, "tier": "T2"},
}

DEFAULT_TIER = {"rent": 1700, "cap": 0.0625, "hard": 188000, "ins": 1100, "tax": 1800, "tier": "T2"}


def parse_acres(acres_str):
    """Best-effort acreage extraction; returns None if not parseable."""
    if not acres_str:
        return None
    try:
        return float(acres_str)
    except (TypeError, ValueError):
        m = re.search(r"(\d+\.?\d*)", str(acres_str))
        return float(m.group(1)) if m else None


def parse_price(price_str):
    """Extract first dollar number from a price string. None if not parseable."""
    if not price_str or price_str.upper() == "TBV":
        return None
    digits = re.sub(r"[^\d]", "", price_str.split("(")[0])  # drop "( $/ac)" suffix
    try:
        return int(digits) if digits else None
    except ValueError:
        return None


def estimate_units(parcel):
    """Try ledger Notes first ('240u', '287 units'); otherwise estimate from acreage."""
    notes = (parcel.get("notes") or "").lower()
    m = re.search(r"(\d{2,4})\s*(?:u\b|units|unit\b|du\b|doors)", notes)
    if m:
        v = int(m.group(1))
        if 50 <= v <= 1500:
            return v
    ac = parse_acres(parcel["acres"])
    if ac:
        # default 12 du/ac net for moderate-density MF
        return max(50, int(ac * 12))
    return 200  # fallback


def enrich_parcel_for_proforma(parcel):
    defaults = MARKET_DEFAULTS.get(parcel["market"], DEFAULT_TIER)
    units = estimate_units(parcel)
    asking = parse_price(parcel["price"])
    acres = parse_acres(parcel["acres"])

    if asking is not None:
        land = asking
    elif acres is not None:
        # Use $100k/ac placeholder (mid-range) when no asking price
        land = int(acres * 100000)
    else:
        land = 3_000_000

    return {
        **parcel,
        "pf_units": units,
        "pf_rent": defaults["rent"],
        "pf_hard": defaults["hard"],
        "pf_land": land,
        "pf_cap": defaults["cap"],
        "pf_ins": defaults["ins"],
        "pf_tax": defaults["tax"],
        "pf_tier": defaults["tier"],
    }


# ============================================================================
# Render landing page
# ============================================================================
def render_index(runs, today_parcels, all_parcels, market_intel, site_root: Path):
    if not runs:
        return None

    latest_date, _ = runs[0]
    latest_url = f"runs/{latest_date}/index.html"

    today_data = [enrich_parcel_for_proforma(p) for p in today_parcels]
    all_data = [enrich_parcel_for_proforma(p) for p in all_parcels]
    runs_list = [d for d, _ in runs]

    sidebar_items_html = "\n".join(_sidebar_item(d, d == latest_date) for d, _ in runs)

    # Per-market default tier info (for pro forma defaults shown in market reports)
    market_defaults_export = {name: defaults for name, defaults in MARKET_DEFAULTS.items()}

    page = INDEX_TEMPLATE.format(
        latest_date=latest_date,
        latest_url=latest_url,
        run_count=len(runs),
        sidebar_items=sidebar_items_html,
        runs_json=json.dumps(runs_list),
        today_parcels_json=json.dumps(today_data),
        all_parcels_json=json.dumps(all_data),
        markets_json=json.dumps([
            {"name": m["name"], "state": m["state"], "ll": m["ll"]}
            for m in MARKETS
        ]),
        market_groups_json=json.dumps(GROUPS),
        market_intel_json=json.dumps(market_intel),
        market_defaults_json=json.dumps(market_defaults_export),
    )

    out = site_root / "index.html"
    out.write_text(page)
    print(f"  wrote {out} ({len(page):,} bytes)")
    return out


def _sidebar_item(d, is_latest):
    active_attr = ' class="active"' if is_latest else ''
    pill = ' <span class="latest">latest</span>' if is_latest else ''
    return (
        f'    <li><a href="#" data-run="runs/{d}/index.html" data-date="{d}"{active_attr}>'
        f'<span class="dot"></span><span class="d">{d}</span>{pill}</a></li>'
    )


# ============================================================================
# Main
# ============================================================================
def main():
    reports_root = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_REPORTS_ROOT
    site_root = Path(__file__).resolve().parent

    print(f"Reports root: {reports_root}")
    print(f"Site root:    {site_root}")

    if not reports_root.exists():
        print(f"ERROR: reports root not found: {reports_root}", file=sys.stderr)
        sys.exit(1)

    runs = find_runs(reports_root)
    print(f"\nFound {len(runs)} runs:")
    for d, _ in runs:
        print(f"  - {d}")

    print("\nCopying dashboards:")
    copy_dashboards(runs, site_root)

    print("\nParsing parcel ledger:")
    all_parcels = parse_ledger(reports_root)
    print(f"  loaded {len(all_parcels)} parcels")

    latest_date = runs[0][0] if runs else None
    today_parcels, history = split_today_vs_history(all_parcels, latest_date) if latest_date else ([], all_parcels)
    print(f"  today's parcels: {len(today_parcels)} (date {latest_date})")
    print(f"  history: {len(history)}")

    print("\nParsing market intel:")
    market_intel = parse_market_intel(reports_root)
    print(f"  loaded intel for {len(market_intel)} markets")

    print("\nWriting landing page:")
    render_index(runs, today_parcels, all_parcels, market_intel, site_root)

    print("\nSite built successfully.")
    print("Next: ./deploy.sh")


if __name__ == "__main__":
    main()
