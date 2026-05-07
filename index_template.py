"""Wrapper landing page template — sidebar + iframe with tab injection.

This template is loaded by build_site.py and rendered with run/parcel data.
The wrapper is intentionally simple: it just shows a sidebar of dates and an
iframe containing the dated dashboard. After the iframe loads, JavaScript
injects three new tabs INTO the iframe's existing tab navigation:

  • Parcel Map    — Leaflet/OSM map with today/all-time toggle
  • Pro Forma+    — replaces the static Pro Forma tab content with the
                    interactive calculator (parcel dropdown + editable inputs)
  • Market Report — pick a market, see a report assembled from the parcel
                    ledger + market intel + aggregator deep-links

Same-origin trust between wrapper and iframe lets us inject CSS/JS/DOM
directly. Old archived dashboards get the new tabs uniformly without
modifying the dashboard files themselves.
"""

INDEX_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Oracle — Neyland Development</title>
<style>
:root {{
  color-scheme: light;
  --navy: #1F3864;
  --gold: #BF9000;
  --bg: #f5f5f7;
  --paper: #ffffff;
  --line: #e3e3e6;
  --ink: #1a1a1a;
  --ink2: #5a5a60;
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; height: 100%; overflow: hidden; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background: var(--bg);
  color: var(--ink);
  font-size: 14px;
  display: grid;
  grid-template-columns: 280px 1fr;
  grid-template-rows: 64px 1fr;
  grid-template-areas: "head head" "side main";
  height: 100vh;
}}
header.brand {{
  grid-area: head;
  background: var(--navy);
  color: white;
  border-bottom: 4px solid var(--gold);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}}
header.brand h1 {{ margin: 0; font-size: 18px; font-weight: 700; letter-spacing: 0.4px; }}
header.brand .sub {{ font-size: 12px; opacity: 0.85; margin-top: 2px; }}
header.brand .meta {{ font-size: 12px; opacity: 0.85; text-align: right; }}
aside.sidebar {{
  grid-area: side;
  background: var(--paper);
  border-right: 1px solid var(--line);
  overflow-y: auto;
  padding: 16px 0;
}}
aside.sidebar h2 {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px;
  color: var(--ink2); margin: 8px 20px 10px; font-weight: 600; }}
aside.sidebar ul {{ list-style: none; margin: 0; padding: 0; }}
aside.sidebar li a {{
  display: flex; align-items: center; gap: 10px; padding: 10px 20px;
  color: var(--ink); text-decoration: none; font-size: 13.5px;
  border-left: 3px solid transparent;
}}
aside.sidebar li a:hover {{ background: #f7f7fa; }}
aside.sidebar li a.active {{
  background: #f0f3f8; border-left-color: var(--gold);
  font-weight: 600; color: var(--navy);
}}
aside.sidebar li a .dot {{ width: 8px; height: 8px; border-radius: 50%; background: #cbd0d8; }}
aside.sidebar li a.active .dot {{ background: var(--gold); }}
aside.sidebar li a .d {{ flex: 1; font-variant-numeric: tabular-nums; }}
aside.sidebar li a .latest {{
  background: var(--gold); color: white; font-size: 10px;
  padding: 2px 7px; border-radius: 10px; font-weight: 700; text-transform: uppercase;
}}
aside.sidebar .footer {{
  margin-top: 20px; padding: 16px 20px; border-top: 1px solid var(--line);
  font-size: 11px; color: var(--ink2); line-height: 1.6;
}}
main.viewer {{
  grid-area: main;
  position: relative;
  background: white;
  overflow: hidden;
}}
main.viewer iframe {{ width: 100%; height: 100%; border: 0; display: block; }}
.toolbar {{
  position: absolute; top: 12px; right: 18px; z-index: 5;
  display: flex; gap: 8px;
}}
.toolbar a {{
  background: white; border: 1px solid var(--line); border-radius: 6px;
  padding: 6px 12px; font-size: 12px; font-weight: 600; color: var(--navy);
  text-decoration: none; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}}
.toolbar a:hover {{ background: #f7f7fa; }}

@media (max-width: 760px) {{
  body {{
    grid-template-columns: 1fr;
    grid-template-rows: 64px 200px 1fr;
    grid-template-areas: "head" "side" "main";
  }}
  aside.sidebar {{ border-right: 0; border-bottom: 1px solid var(--line); }}
}}
</style>
</head>
<body>
<header class="brand">
  <div>
    <h1>ORACLE — Site-Sourcing Intelligence</h1>
    <div class="sub">Neyland Development · Daily Multifamily Land Sourcing</div>
  </div>
  <div class="meta">{run_count} runs archived<br>Latest: <strong>{latest_date}</strong></div>
</header>

<aside class="sidebar">
  <h2>Run Archive</h2>
  <ul id="runlist">
{sidebar_items}
  </ul>
  <div class="footer">
    Built from <code>Oracle Reports/</code><br>
    Auto-deploys after each scheduled run.<br>
    Confidential — internal use only.
  </div>
</aside>

<main class="viewer">
  <div class="toolbar">
    <a id="open-new-tab" href="{latest_url}" target="_blank" rel="noopener">Open ↗</a>
  </div>
  <iframe id="viewer-frame" src="{latest_url}" title="Oracle Dashboard"></iframe>
</main>

<script>
// ============ Data injected at build time ============
const RUNS              = {runs_json};
const TODAY_PARCELS     = {today_parcels_json};
const ALL_PARCELS       = {all_parcels_json};
const MARKETS_DATA      = {markets_json};
const MARKET_GROUPS     = {market_groups_json};
const MARKET_INTEL      = {market_intel_json};
const MARKET_DEFAULTS   = {market_defaults_json};

// ============ Sidebar / iframe routing ============
const links = document.querySelectorAll('#runlist a');
const frame = document.getElementById('viewer-frame');
const openLink = document.getElementById('open-new-tab');

function selectRun(href, date) {{
  frame.src = href;
  openLink.href = href;
  links.forEach(a => a.classList.remove('active'));
  const t = Array.from(links).find(a => a.dataset.date === date);
  if (t) t.classList.add('active');
  history.replaceState(null, '', '#' + date);
}}

links.forEach(a => a.addEventListener('click', e => {{
  e.preventDefault();
  selectRun(a.dataset.run, a.dataset.date);
}}));

const initialHash = location.hash.replace('#', '');
if (initialHash && RUNS.includes(initialHash)) {{
  selectRun(`runs/${{initialHash}}/index.html`, initialHash);
}}

// ============ Iframe injection: add new tabs to the dashboard ============
frame.addEventListener('load', () => injectIntoIframe());

function injectIntoIframe() {{
  const doc = frame.contentDocument;
  const win = frame.contentWindow;
  if (!doc || !doc.querySelector('nav.tabs')) {{
    // Some legacy archives may not have nav.tabs; skip injection on those
    return;
  }}

  // ===== 1. Inject Leaflet (CSS+JS) into iframe head =====
  if (!doc.querySelector('link[data-injected=leaflet]')) {{
    const lcss = doc.createElement('link');
    lcss.rel = 'stylesheet';
    lcss.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    lcss.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
    lcss.crossOrigin = '';
    lcss.dataset.injected = 'leaflet';
    doc.head.appendChild(lcss);
  }}

  const finishInjection = () => {{
    addInjectedStyles(doc);
    addNewTabs(doc, win);
    rebindTabs(doc);
  }};

  if (win.L) {{
    finishInjection();
  }} else {{
    const ljs = doc.createElement('script');
    ljs.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    ljs.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
    ljs.crossOrigin = '';
    ljs.onload = finishInjection;
    doc.head.appendChild(ljs);
  }}
}}

// CSS scoped to the injected tab content
function addInjectedStyles(doc) {{
  if (doc.querySelector('style[data-injected=oracle]')) return;
  const style = doc.createElement('style');
  style.dataset.injected = 'oracle';
  style.textContent = `
.injected-pane {{ padding: 24px; max-width: 1400px; margin: 0 auto; }}
.injected-pane h3 {{ color: #1F3864; border-bottom: 2px solid #BF9000;
  padding-bottom: 6px; display: inline-block; margin-top: 24px; }}
.injected-pane h3:first-child {{ margin-top: 0; }}

/* Map tab */
.map-wrap {{ display: flex; flex-direction: column; height: calc(100vh - 130px); margin: 0; padding: 0; max-width: none; }}
.map-toolbar {{ background: #fff; padding: 12px 20px; border-bottom: 1px solid #e3e3e6;
  display: flex; gap: 12px; align-items: center; flex-shrink: 0; }}
.map-toolbar .toggle {{ display: flex; border: 1px solid #e3e3e6; border-radius: 6px; overflow: hidden; }}
.map-toolbar .toggle button {{ background: white; border: 0; padding: 8px 16px;
  font-size: 13px; cursor: pointer; color: #5a5a60; font-family: inherit; }}
.map-toolbar .toggle button.active {{ background: #1F3864; color: white; font-weight: 700; }}
.map-toolbar .legend {{ display: flex; gap: 14px; align-items: center; font-size: 12px; color: #5a5a60; }}
.map-toolbar .legend .swatch {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; vertical-align: middle; margin-right: 4px; }}
.map-toolbar .count {{ margin-left: auto; font-size: 12px; color: #5a5a60; }}
.leaflet-container {{ flex: 1; min-height: 0; }}
.leaflet-popup-content {{ font-size: 13px; line-height: 1.5; }}
.leaflet-popup-content h4 {{ margin: 0 0 6px; color: #1F3864; font-size: 14px; }}
.leaflet-popup-content .meta {{ color: #5a5a60; margin: 4px 0; }}
.leaflet-popup-content a {{ color: #1F3864; }}

/* Pro Forma calculator */
.pf-grid {{ display: grid; grid-template-columns: 380px 1fr; gap: 24px; }}
.pf-card {{ background: #fff; border: 1px solid #e3e3e6; border-radius: 8px; padding: 20px; }}
.pf-card label {{ display: block; font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.6px; color: #5a5a60; margin: 14px 0 4px; font-weight: 700; }}
.pf-card label:first-of-type {{ margin-top: 0; }}
.pf-card select, .pf-card input[type=number] {{
  width: 100%; padding: 9px 12px; border: 1px solid #e3e3e6; border-radius: 6px;
  font-size: 14px; font-family: inherit; background: white;
}}
.pf-card select:focus, .pf-card input:focus {{ outline: none; border-color: #1F3864; }}
.pf-meta {{ background: #f7f7fa; padding: 10px 12px; border-radius: 6px; margin: 10px 0;
  font-size: 12.5px; color: #5a5a60; line-height: 1.5; }}
.pf-meta strong {{ color: #1F3864; }}
.pf-results {{ display: flex; flex-direction: column; gap: 14px; }}
.pf-summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
.pf-kpi {{ background: #fff; border: 1px solid #e3e3e6; border-radius: 8px; padding: 14px; }}
.pf-kpi label {{ font-size: 10px; text-transform: uppercase; letter-spacing: 0.6px;
  color: #5a5a60; display: block; margin-bottom: 4px; font-weight: 700; }}
.pf-kpi .v {{ font-size: 22px; font-weight: 700; color: #1F3864; }}
.pf-kpi .vsub {{ font-size: 12px; color: #5a5a60; margin-top: 2px; }}
.pf-scenarios {{ background: #fff; border: 1px solid #e3e3e6; border-radius: 8px; padding: 16px; }}
table.pf-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
table.pf-table th {{ background: #1F3864; color: white; padding: 9px 12px; text-align: left;
  font-weight: 600; font-size: 12px; }}
table.pf-table td {{ padding: 9px 12px; border-bottom: 1px solid #e3e3e6; }}
table.pf-table tr:hover td {{ background: #fafafa; }}
.verdict {{ padding: 3px 10px; border-radius: 10px; font-size: 11px; font-weight: 700; color: white; display: inline-block; }}
.v-proceed-comfort {{ background: #1b5e20; }}
.v-proceed {{ background: #2e7d32; }}
.v-conditional {{ background: #bf9000; }}
.v-borderline {{ background: #e65100; }}
.v-does-not-pencil {{ background: #b71c1c; }}
.pf-footnote {{ font-size: 11.5px; color: #5a5a60; padding: 12px 14px; background: #fff8e1;
  border-left: 3px solid #BF9000; border-radius: 4px; margin-top: 10px; }}

/* Market Report */
.mkt-picker {{ background: #fff; border: 1px solid #e3e3e6; border-radius: 8px; padding: 20px; margin-bottom: 16px; }}
.mkt-picker select {{ width: 100%; padding: 11px 14px; font-size: 14px;
  border: 1px solid #e3e3e6; border-radius: 6px; background: white; font-family: inherit; }}
.mkt-report {{ display: flex; flex-direction: column; gap: 16px; }}
.mkt-card {{ background: #fff; border: 1px solid #e3e3e6; border-radius: 8px; padding: 20px; }}
.mkt-card h3 {{ margin-top: 0; }}
.mkt-summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px; margin-top: 10px; }}
.mkt-kpi {{ background: #f7f7fa; padding: 10px 12px; border-radius: 6px; }}
.mkt-kpi label {{ font-size: 10px; text-transform: uppercase; color: #5a5a60; font-weight: 700; }}
.mkt-kpi .v {{ font-size: 16px; font-weight: 700; color: #1F3864; }}
.mkt-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
.mkt-table th {{ background: #1F3864; color: white; padding: 8px 10px; text-align: left; font-size: 12px; }}
.mkt-table td {{ padding: 8px 10px; border-bottom: 1px solid #e3e3e6; vertical-align: top; }}
.mkt-table tr:hover td {{ background: #fafafa; }}
.mkt-intel-block {{ margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px dashed #e3e3e6; }}
.mkt-intel-block:last-child {{ border-bottom: 0; }}
.mkt-intel-block .dt {{ font-size: 11px; color: #BF9000; font-weight: 700; text-transform: uppercase; }}
.mkt-intel-block .hd {{ font-weight: 700; color: #1F3864; font-size: 13.5px; margin: 4px 0 6px; }}
.mkt-intel-block ul {{ margin: 0 0 0 18px; padding: 0; font-size: 13px; line-height: 1.55; }}
.mkt-intel-block li {{ margin-bottom: 4px; }}
.aggregator-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px; margin-top: 10px; }}
.agg-card {{ background: white; border: 1px solid #e3e3e6; border-radius: 8px; padding: 14px;
  display: flex; flex-direction: column; gap: 6px; cursor: pointer; text-decoration: none; color: #1a1a1a; }}
.agg-card:hover {{ border-color: #1F3864; box-shadow: 0 4px 12px rgba(31,56,100,0.1); }}
.agg-card .agg-name {{ font-weight: 700; color: #1F3864; font-size: 14px; }}
.agg-card .agg-desc {{ font-size: 12px; color: #5a5a60; }}
.agg-card .agg-arrow {{ color: #BF9000; font-size: 14px; margin-top: auto; align-self: flex-end; }}
.empty {{ color: #5a5a60; font-style: italic; padding: 12px 0; }}
  `;
  doc.head.appendChild(style);
}}

// Add 3 new tab buttons to the dashboard's nav.tabs and 3 new section panels
function addNewTabs(doc, win) {{
  const nav = doc.querySelector('nav.tabs');
  const main = doc.querySelector('main');
  if (!nav || !main) return;

  const newTabs = [
    {{ id: 'inj-map',     label: 'Parcel Map' }},
    {{ id: 'inj-pf',      label: 'Pro Forma+' }},
    {{ id: 'inj-mkt',     label: 'Market Report' }},
  ];

  newTabs.forEach(t => {{
    if (doc.getElementById(t.id)) return; // already injected (e.g. on tab switch)
    const btn = doc.createElement('button');
    btn.dataset.tab = t.id;
    btn.dataset.injected = '1';
    btn.textContent = t.label;
    nav.appendChild(btn);

    const sect = doc.createElement('section');
    sect.id = t.id;
    sect.className = 'tab-panel';
    main.appendChild(sect);
  }});

  buildMapPane(doc, win, doc.getElementById('inj-map'));
  buildPFPane(doc, win, doc.getElementById('inj-pf'));
  buildMktPane(doc, win, doc.getElementById('inj-mkt'));
}}

// Re-attach click handlers across ALL tab buttons (existing + injected) so the
// dashboard's original handler stops being the only authority.
function rebindTabs(doc) {{
  const tabs = doc.querySelectorAll('nav.tabs button');
  const panels = doc.querySelectorAll('.tab-panel');
  tabs.forEach(btn => {{
    const fresh = btn.cloneNode(true);
    btn.parentNode.replaceChild(fresh, btn);
    fresh.addEventListener('click', () => {{
      doc.querySelectorAll('nav.tabs button').forEach(x => x.classList.remove('active'));
      doc.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      fresh.classList.add('active');
      const target = doc.getElementById(fresh.dataset.tab);
      if (target) target.classList.add('active');
    }});
  }});
}}

// ============ Tab content builders ============
function statusColor(status) {{
  const s = (status || '').toUpperCase();
  if (s.startsWith('LOST') || s.startsWith('KILLED')) return '#b71c1c';
  if (s.startsWith('PRO_FORMA')) return '#1565c0';
  if (s.startsWith('WATCH') || s.startsWith('UPDATE')) return '#bf9000';
  return '#2e7d32';
}}

function jitter(lat, lng, idx) {{
  const a = idx * 137.5 * Math.PI / 180;
  const f = Math.min(0.6, 0.06 + (idx * 0.01));
  const r = 0.025;
  return [lat + Math.cos(a) * r * f, lng + Math.sin(a) * r * f];
}}

function buildMapPane(doc, win, pane) {{
  pane.innerHTML = `
<div class="map-wrap">
  <div class="map-toolbar">
    <div class="toggle" id="inj-map-toggle">
      <button class="active" data-scope="today">Today's Parcels</button>
      <button data-scope="all">All-time Ledger</button>
    </div>
    <div class="legend">
      <span><span class="swatch" style="background:#2e7d32"></span>NEW</span>
      <span><span class="swatch" style="background:#1565c0"></span>PRO FORMA RUN</span>
      <span><span class="swatch" style="background:#bf9000"></span>WATCH / UPDATE</span>
      <span><span class="swatch" style="background:#b71c1c"></span>LOST / KILLED</span>
    </div>
    <div class="count" id="inj-map-count"></div>
  </div>
  <div id="inj-leaflet-map"></div>
</div>`;

  let mapInst, layer;
  function render(scope) {{
    if (!win.L) return;
    if (!mapInst) {{
      mapInst = win.L.map(doc.getElementById('inj-leaflet-map'), {{ scrollWheelZoom: true }})
        .setView([32.5, -83.5], 6);
      win.L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        attribution: '&copy; OpenStreetMap', maxZoom: 19,
      }}).addTo(mapInst);
      layer = win.L.layerGroup().addTo(mapInst);
    }}
    layer.clearLayers();
    const data = scope === 'all' ? ALL_PARCELS : TODAY_PARCELS;
    const byCity = {{}};
    data.forEach(p => {{
      const k = p.lat + ',' + p.lng;
      (byCity[k] = byCity[k] || []).push(p);
    }});
    let total = 0;
    Object.values(byCity).forEach(group => {{
      group.forEach((p, i) => {{
        total += 1;
        const ll = group.length > 1 ? jitter(p.lat, p.lng, i) : [p.lat, p.lng];
        const marker = win.L.circleMarker(ll, {{
          radius: Math.max(6, Math.min(14, (p.score || 60) / 9)),
          fillColor: statusColor(p.status),
          color: 'white', weight: 2, opacity: 1, fillOpacity: 0.85,
        }});
        const url = p.url ? `<a href="${{p.url}}" target="_blank" rel="noopener">View listing →</a>` : '';
        marker.bindPopup(`
          <h4>${{p.market}}</h4>
          <div><strong>${{p.locator || ''}}</strong></div>
          <div class="meta">Score ${{p.score || '—'}} · ${{p.status || ''}} · ${{p.acres || '—'}} ac · Friction ${{p.friction || '—'}}/10</div>
          <div class="meta">${{p.zoning || ''}}</div>
          <div class="meta">${{p.price || ''}}</div>
          <div>${{url}}</div>
        `);
        layer.addLayer(marker);
      }});
    }});
    doc.getElementById('inj-map-count').textContent = total + ' parcel' + (total === 1 ? '' : 's') + ' shown';
    if (total > 0) {{
      const bounds = win.L.latLngBounds(data.map(p => [p.lat, p.lng]));
      mapInst.fitBounds(bounds.pad(0.15), {{ maxZoom: 8 }});
    }}
  }}

  pane.querySelectorAll('#inj-map-toggle button').forEach(b => {{
    b.addEventListener('click', () => {{
      pane.querySelectorAll('#inj-map-toggle button').forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      render(b.dataset.scope);
    }});
  }});

  // Render once the map is actually visible (Leaflet needs container size)
  pane.querySelector('.map-toolbar').addEventListener('focus', () => render('today'));
  setTimeout(() => render('today'), 100);
  // Also re-render on tab activation
  const navObs = new MutationObserver(() => {{
    if (pane.classList.contains('active') && mapInst) mapInst.invalidateSize();
  }});
  navObs.observe(pane, {{ attributes: true, attributeFilter: ['class'] }});
}}

function fmtMoney(n) {{
  if (!isFinite(n)) return '—';
  if (Math.abs(n) >= 1e6) return '$' + (n/1e6).toFixed(2) + 'M';
  if (Math.abs(n) >= 1e3) return '$' + (n/1e3).toFixed(0) + 'k';
  return '$' + Math.round(n).toLocaleString();
}}
function fmtPct(p) {{ return (p*100).toFixed(2) + '%'; }}
function fmtBps(p) {{ return (p>=0?'+':'') + (p*100).toFixed(0) + ' bps'; }}
function verdictFor(yoc) {{
  if (yoc >= 0.060) return ['PROCEED COMFORT', 'v-proceed-comfort'];
  if (yoc >= 0.055) return ['PROCEED',         'v-proceed'];
  if (yoc >= 0.050) return ['CONDITIONAL',     'v-conditional'];
  if (yoc >= 0.045) return ['BORDERLINE',      'v-borderline'];
  return                    ['DOES NOT PENCIL','v-does-not-pencil'];
}}
function calcCase(units, rent, land, hard, ins, tax, capRate, vacancy, opexRatio) {{
  const annualGrossRent = rent * 12 * units;
  const egr = annualGrossRent * (1 - vacancy);
  const baseOpEx = egr * opexRatio;
  const fixedOpEx = (tax + ins) * units;
  const opex = baseOpEx + fixedOpEx;
  const noi = egr - opex;
  const tdc = land + hard * units * 1.14;
  const yoc = tdc > 0 ? noi / tdc : 0;
  return {{ noi, tdc, yoc, spread: yoc - capRate, egr, opex }};
}}

function buildPFPane(doc, win, pane) {{
  pane.innerHTML = `
<div class="injected-pane">
  <div class="pf-grid">
    <div class="pf-card">
      <h3>Inputs</h3>
      <label>Pick a parcel from today's run</label>
      <select id="inj-pf-parcel"></select>
      <div class="pf-meta" id="inj-pf-meta"></div>
      <label>Units (estimated)</label>
      <input id="inj-pf-units" type="number" min="20" max="2000" step="1">
      <label>Blended rent ($/mo)</label>
      <input id="inj-pf-rent" type="number" min="800" max="5000" step="25">
      <label>Land basis (total $)</label>
      <input id="inj-pf-land" type="number" min="0" step="50000">
      <label>Hard cost ($/unit)</label>
      <input id="inj-pf-hard" type="number" min="100000" max="350000" step="5000">
      <label>Insurance ($/unit/yr)</label>
      <input id="inj-pf-ins" type="number" min="500" max="5000" step="50">
      <label>Exit cap rate (%)</label>
      <input id="inj-pf-cap" type="number" min="3" max="10" step="0.05">
      <div class="pf-footnote">Numbers update live. Defaults derived from market intel.
        Replace with broker-confirmed values before any LOI.</div>
    </div>
    <div class="pf-results">
      <div class="pf-summary">
        <div class="pf-kpi"><label>YoC (BASE)</label><div class="v" id="inj-kpi-yoc">—</div><div class="vsub" id="inj-kpi-yoc-verdict"></div></div>
        <div class="pf-kpi"><label>NOI</label><div class="v" id="inj-kpi-noi">—</div><div class="vsub">stabilized annual</div></div>
        <div class="pf-kpi"><label>TDC</label><div class="v" id="inj-kpi-tdc">—</div><div class="vsub" id="inj-kpi-tdc-perunit">—/u</div></div>
        <div class="pf-kpi"><label>Spread</label><div class="v" id="inj-kpi-spread">—</div><div class="vsub">YoC − exit cap</div></div>
      </div>
      <div class="pf-scenarios">
        <h3>Scenarios</h3>
        <table class="pf-table">
          <thead><tr><th>Scenario</th><th>YoC</th><th>vs BASE</th><th>Verdict</th><th>Assumption Δ</th></tr></thead>
          <tbody id="inj-pf-rows"></tbody>
        </table>
        <div class="pf-footnote">Verdict thresholds: ≥6.0% PROCEED COMFORT · 5.5–6.0% PROCEED · 5.0–5.5% CONDITIONAL · 4.5–5.0% BORDERLINE · &lt;4.5% DOES NOT PENCIL.</div>
      </div>
    </div>
  </div>
</div>`;

  const sel = pane.querySelector('#inj-pf-parcel');
  TODAY_PARCELS.forEach((p, i) => {{
    const opt = doc.createElement('option');
    opt.value = i;
    const tag = p.rank ? `[${{p.rank}}] ` : '';
    opt.textContent = `${{tag}}${{p.market}} — ${{p.locator}} (score ${{p.score || '—'}})`;
    sel.appendChild(opt);
  }});

  const get = id => pane.querySelector('#' + id);
  const inputs = ['inj-pf-units','inj-pf-rent','inj-pf-land','inj-pf-hard','inj-pf-ins','inj-pf-cap'].map(get);

  function loadParcel(idx) {{
    const p = TODAY_PARCELS[idx];
    if (!p) return;
    get('inj-pf-units').value = p.pf_units;
    get('inj-pf-rent').value  = p.pf_rent;
    get('inj-pf-land').value  = p.pf_land;
    get('inj-pf-hard').value  = p.pf_hard;
    get('inj-pf-ins').value   = p.pf_ins;
    get('inj-pf-cap').value   = (p.pf_cap * 100).toFixed(2);
    get('inj-pf-meta').innerHTML = `
      <strong>${{p.market}}</strong> — ${{p.locator}}<br>
      Acres: ${{p.acres || '—'}} · Zoning: ${{p.zoning || '—'}} · Score ${{p.score || '—'}} · Friction ${{p.friction || '—'}}/10<br>
      Listing price: ${{p.price || 'TBV'}} · Tier: ${{p.pf_tier || '—'}}
    `;
    recalc();
  }}

  function recalc() {{
    const units = parseFloat(get('inj-pf-units').value) || 0;
    const rent  = parseFloat(get('inj-pf-rent').value)  || 0;
    const land  = parseFloat(get('inj-pf-land').value)  || 0;
    const hard  = parseFloat(get('inj-pf-hard').value)  || 0;
    const ins   = parseFloat(get('inj-pf-ins').value)   || 0;
    const cap   = (parseFloat(get('inj-pf-cap').value)  || 0) / 100;
    const idx = parseInt(sel.value, 10) || 0;
    const tax = (TODAY_PARCELS[idx] && TODAY_PARCELS[idx].pf_tax) || 2200;

    const base = calcCase(units, rent, land, hard, ins, tax, cap, 0.05, 0.14);
    get('inj-kpi-yoc').textContent = fmtPct(base.yoc);
    get('inj-kpi-noi').textContent = fmtMoney(base.noi);
    get('inj-kpi-tdc').textContent = fmtMoney(base.tdc);
    get('inj-kpi-tdc-perunit').textContent = fmtMoney(base.tdc/units) + ' / unit';
    get('inj-kpi-spread').textContent = fmtBps(base.spread);
    const [verdict, cls] = verdictFor(base.yoc);
    get('inj-kpi-yoc-verdict').innerHTML = `<span class="verdict ${{cls}}">${{verdict}}</span>`;

    const scenarios = [
      {{ name: 'BASE',           res: base, delta: 'as entered' }},
      {{ name: 'RECESSION',      res: calcCase(units, rent, land, hard, ins, tax, cap+0.0075, 0.06, 0.14), delta: 'exit cap +75bps · vac 6%' }},
      {{ name: 'COST SPIKE',     res: calcCase(units, rent, land, hard*1.12, ins, tax, cap, 0.05, 0.14), delta: 'hard cost +12%' }},
      {{ name: 'LEASE-UP DELAY', res: calcCase(units, rent, land, hard, ins, tax, cap, 0.07, 0.16), delta: 'vac 7% · OpEx +200bps' }},
      {{ name: 'INSURANCE 2x',   res: calcCase(units, rent, land, hard, ins*2, tax, cap, 0.05, 0.14), delta: `ins ${{(ins*2).toLocaleString()}}/u` }},
      {{ name: 'UPSIDE',         res: calcCase(units, rent*1.05, land*0.80, hard, ins, tax, cap, 0.04, 0.13), delta: 'rent +5% · land −20%' }},
    ];
    const tbody = pane.querySelector('#inj-pf-rows');
    tbody.innerHTML = scenarios.map(s => {{
      const [v, c] = verdictFor(s.res.yoc);
      const vs = s.name === 'BASE' ? '—' : fmtBps(s.res.yoc - base.yoc);
      return `<tr>
        <td><strong>${{s.name}}</strong></td>
        <td>${{fmtPct(s.res.yoc)}}</td>
        <td>${{vs}}</td>
        <td><span class="verdict ${{c}}">${{v}}</span></td>
        <td style="color:#5a5a60;font-size:12px">${{s.delta}}</td>
      </tr>`;
    }}).join('');
  }}

  sel.addEventListener('change', () => loadParcel(parseInt(sel.value, 10)));
  inputs.forEach(el => el.addEventListener('input', recalc));
  if (TODAY_PARCELS.length > 0) {{
    sel.value = '0';
    loadParcel(0);
  }}
}}

function buildMktPane(doc, win, pane) {{
  // Build dropdown options grouped
  let optsHTML = '<option value="">— Pick a market to generate a report —</option>';
  MARKET_GROUPS.forEach(([groupName, marketNames]) => {{
    optsHTML += `<optgroup label="${{groupName}}">`;
    marketNames.forEach(name => {{
      optsHTML += `<option value="${{name.replace(/"/g, '&quot;')}}">${{name}}</option>`;
    }});
    optsHTML += '</optgroup>';
  }});
  pane.innerHTML = `
<div class="injected-pane">
  <div class="mkt-picker">
    <h3 style="margin-top:0">Market Report</h3>
    <p style="color:#5a5a60;font-size:13px;margin:6px 0 14px">
      Pick a market — Oracle assembles a report from the parcel ledger, persistent market intel,
      and pre-filtered aggregator deep links.
    </p>
    <select id="inj-mkt-select">${{optsHTML}}</select>
  </div>
  <div id="inj-mkt-out"></div>
</div>`;

  const out = pane.querySelector('#inj-mkt-out');
  const sel = pane.querySelector('#inj-mkt-select');

  sel.addEventListener('change', () => {{
    const marketName = sel.value;
    if (!marketName) {{ out.innerHTML = ''; return; }}
    out.innerHTML = renderMarketReport(marketName);
  }});
}}

function aggregatorURLs(marketName, state) {{
  const primary = marketName.split('/')[0].split('(')[0].split(',')[0].trim();
  const slug = primary.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
  const stateSlug = ({{
    AL:'alabama', FL:'florida', GA:'georgia', KY:'kentucky', MS:'mississippi',
    NC:'north-carolina', SC:'south-carolina', TN:'tennessee'
  }})[state] || '';
  const stateLower = (state || '').toLowerCase();
  const cityCap = primary.charAt(0).toUpperCase() + primary.slice(1).toLowerCase();
  return [
    {{ name: 'LoopNet',      desc: 'Multifamily properties in this market', url: `https://www.loopnet.com/search/multifamily-properties/${{slug}}-${{stateLower}}/for-sale/` }},
    {{ name: 'Crexi',        desc: 'Multifamily commercial listings',        url: `https://www.crexi.com/properties/${{state}}/${{cityCap.replace(/\s+/g, '_')}}/Multifamily` }},
    {{ name: 'LandWatch',    desc: 'Land for sale in this market',           url: `https://www.landwatch.com/${{stateSlug}}-land-for-sale/${{slug}}` }},
    {{ name: 'Land.com',     desc: 'All land listings — county-wide',        url: `https://www.land.com/${{cityCap.replace(/\s+/g, '-')}}-${{state}}/all-land/` }},
    {{ name: 'Homes.com',    desc: 'Multi-family + land in this market',     url: `https://www.homes.com/${{slug}}-${{stateLower}}/multi-family-homes-for-sale/` }},
    {{ name: 'LandSearch',   desc: 'All listings in this metro',             url: `https://www.landsearch.com/properties/${{slug}}-${{stateLower}}` }},
    {{ name: 'Land & Farm',  desc: 'Cross-listing aggregator',               url: `https://www.landandfarm.com/search/${{stateSlug}}/${{slug}}-land-for-sale/` }},
    {{ name: 'Realtor.com',  desc: 'Residential MLS — surfaces residential MF', url: `https://www.realtor.com/realestateandhomes-search/${{cityCap.replace(/\s+/g, '-')}}_${{state}}/type-multi-family-home` }},
  ];
}}

function renderMarketReport(marketName) {{
  const market = MARKETS_DATA.find(m => m.name === marketName) || {{ name: marketName, state: '', ll: [33,-84] }};
  const defaults = MARKET_DEFAULTS[marketName];
  // All parcels Oracle has surfaced in this market (today + history)
  const allP = ALL_PARCELS.concat(TODAY_PARCELS);
  const seen = new Set();
  const inMarket = allP.filter(p => {{
    const k = p.date + '|' + p.locator + '|' + p.score;
    if (seen.has(k)) return false;
    seen.add(k);
    return p.market === marketName;
  }});
  inMarket.sort((a, b) => (b.date || '').localeCompare(a.date || ''));

  const intel = MARKET_INTEL[marketName] || [];
  const aggs = aggregatorURLs(marketName, market.state);

  // Section: market header summary
  let html = `<div class="mkt-report">`;
  html += `<div class="mkt-card">
    <h3>${{marketName}}</h3>
    <div class="mkt-summary-grid">
      <div class="mkt-kpi"><label>State</label><div class="v">${{market.state || '—'}}</div></div>
      <div class="mkt-kpi"><label>Centroid</label><div class="v" style="font-size:13px">${{market.ll[0].toFixed(3)}}, ${{market.ll[1].toFixed(3)}}</div></div>
      <div class="mkt-kpi"><label>Tier</label><div class="v">${{defaults?.tier || '—'}}</div></div>
      <div class="mkt-kpi"><label>Default rent</label><div class="v">${{defaults ? '$'+defaults.rent+'/mo' : '—'}}</div></div>
      <div class="mkt-kpi"><label>Default exit cap</label><div class="v">${{defaults ? (defaults.cap*100).toFixed(2)+'%' : '—'}}</div></div>
      <div class="mkt-kpi"><label>Default insurance</label><div class="v">${{defaults ? '$'+defaults.ins+'/u' : '—'}}</div></div>
      <div class="mkt-kpi"><label>Parcels surfaced</label><div class="v">${{inMarket.length}}</div></div>
      <div class="mkt-kpi"><label>Intel notes</label><div class="v">${{intel.length}}</div></div>
    </div>
  </div>`;

  // Section: parcels Oracle has surfaced
  html += `<div class="mkt-card"><h3>Parcels Oracle has surfaced in this market (${{inMarket.length}})</h3>`;
  if (inMarket.length === 0) {{
    html += `<div class="empty">None yet — try the aggregator links below to surface inventory manually,
      or run an on-demand Oracle research session.</div>`;
  }} else {{
    html += `<table class="mkt-table"><thead>
      <tr><th>Date</th><th>Score</th><th>Status</th><th>Locator</th><th>Acres</th><th>Zoning</th><th>Price</th><th>Listing</th></tr>
    </thead><tbody>`;
    inMarket.forEach(p => {{
      const link = p.url ? `<a href="${{p.url}}" target="_blank" rel="noopener">↗</a>` : '—';
      html += `<tr>
        <td style="font-variant-numeric:tabular-nums">${{p.date || '—'}}</td>
        <td><strong>${{p.score || '—'}}</strong></td>
        <td style="font-size:11px">${{p.status || ''}}</td>
        <td>${{p.locator || ''}}</td>
        <td>${{p.acres || '—'}}</td>
        <td style="font-size:12px">${{p.zoning || ''}}</td>
        <td style="font-size:12px">${{p.price || 'TBV'}}</td>
        <td>${{link}}</td>
      </tr>`;
    }});
    html += `</tbody></table>`;
  }}
  html += `</div>`;

  // Section: market intel notes
  html += `<div class="mkt-card"><h3>Market intelligence (${{intel.length}} observations)</h3>`;
  if (intel.length === 0) {{
    html += `<div class="empty">No observations yet for this market in the brain.</div>`;
  }} else {{
    intel.forEach(block => {{
      const lines = block.lines.map(l => `<li>${{escapeHTML(l.replace(/^[-*]\s*/, ''))}}</li>`).join('');
      html += `<div class="mkt-intel-block">
        <div class="dt">${{block.date}}</div>
        <div class="hd">${{escapeHTML(block.header)}}</div>
        <ul>${{lines}}</ul>
      </div>`;
    }});
  }}
  html += `</div>`;

  // Section: live aggregator deep links
  html += `<div class="mkt-card"><h3>Run a live search on this market</h3>
    <div style="color:#5a5a60;font-size:13px;margin-bottom:6px">
      Each link opens in a new tab pre-filtered to ${{marketName}}.
    </div>
    <div class="aggregator-grid">`;
  aggs.forEach(a => {{
    html += `<a href="${{a.url}}" target="_blank" rel="noopener" class="agg-card">
      <div class="agg-name">${{a.name}}</div>
      <div class="agg-desc">${{a.desc}}</div>
      <div class="agg-arrow">↗</div>
    </a>`;
  }});
  html += `</div></div>`;

  // Section: trigger fresh Oracle research (manual workflow guidance)
  const promptText = `Oracle: run an ad-hoc research pass on ${{marketName}} only. ` +
    `Surface every actionable multifamily parcel currently listed (LoopNet, Crexi, LandWatch, ` +
    `LandSearch, Land.com, Land & Farm, Homes.com), score each per the v2.2 rubric, ` +
    `cross-verify across at least two aggregators, flag any parcel whose $/acre is materially ` +
    `outside the local comp band, and summarize. Include zoning verification status and ` +
    `next-step recommendation per parcel.`;
  html += `<div class="mkt-card"><h3>Trigger fresh Oracle research</h3>
    <div style="color:#5a5a60;font-size:13px;margin-bottom:10px">
      Copy the prompt below and paste it into a Cowork session to run an ad-hoc Oracle pass on this market only.
      Output deploys back to this site at the next scheduled run, or you can manually run <code>./deploy.sh</code>
      after Oracle finishes.
    </div>
    <textarea readonly id="inj-prompt" style="width:100%;min-height:90px;padding:10px;border:1px solid #e3e3e6;border-radius:6px;font-family:inherit;font-size:12px;color:#1F3864">${{escapeHTML(promptText)}}</textarea>
    <button onclick="navigator.clipboard.writeText(document.getElementById('inj-prompt').value).then(()=>this.textContent='Copied ✓')"
      style="margin-top:10px;background:#1F3864;color:white;border:0;padding:9px 16px;border-radius:6px;font-weight:600;cursor:pointer;font-family:inherit">Copy prompt</button>
  </div>`;

  html += `</div>`;
  return html;
}}

function escapeHTML(s) {{
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}}
</script>
</body>
</html>"""
