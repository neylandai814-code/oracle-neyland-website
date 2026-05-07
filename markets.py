"""
Markets reference data — used by build_site.py to enrich the landing page.

For each market we have:
  - centroid: [lat, lng] — used by the Parcel Map tab to pin parcels at the
    city/county centroid (we don't geocode individual parcel addresses).
  - state: 2-letter state code, used in aggregator URLs.
  - aliases: alternate strings that may appear in parcel ledger market names
    (case-insensitive substring match). The first matching alias wins.

The aggregator URL builders are JS-side (in index.html) so they can update
without a rebuild — see buildAggregatorURLs() in the page script.

If a parcel's market doesn't match any of these, it falls back to a default
state centroid; the parcel still appears in maps/lists but is pinned roughly.
"""

# (lat, lng) centroid + 2-letter state + aliases (substring, case-insensitive)
MARKETS = [
    # ===== Primary focus markets =====
    {"name": "Charleston, SC",          "ll": [32.7765, -79.9311], "state": "SC",
     "aliases": ["charleston"]},
    {"name": "Wilmington, NC",          "ll": [34.2104, -77.8868], "state": "NC",
     "aliases": ["wilmington", "leland", "brunswick county", "new hanover"]},
    {"name": "Greenville-Spartanburg, SC", "ll": [34.8526, -82.3940], "state": "SC",
     "aliases": ["greenville-spartanburg", "greenville sc", "spartanburg"]},
    {"name": "Greenville, SC",          "ll": [34.8526, -82.3940], "state": "SC",
     "aliases": ["greenville, sc", "greenville county"]},
    {"name": "Knoxville, TN",           "ll": [35.9606, -83.9207], "state": "TN",
     "aliases": ["knoxville", "knox county"]},
    {"name": "Chattanooga, TN",         "ll": [35.0456, -85.3097], "state": "TN",
     "aliases": ["chattanooga", "hamilton"]},
    {"name": "Asheville, NC",           "ll": [35.5951, -82.5515], "state": "NC",
     "aliases": ["asheville", "buncombe"]},
    {"name": "Savannah, GA",            "ll": [32.0809, -81.0912], "state": "GA",
     "aliases": ["savannah", "chatham"]},
    {"name": "Augusta, GA",             "ll": [33.4735, -82.0105], "state": "GA",
     "aliases": ["augusta", "richmond county"]},
    {"name": "Columbia, SC",            "ll": [34.0007, -81.0348], "state": "SC",
     "aliases": ["columbia, sc", "richland county"]},
    {"name": "Lakeland, FL",            "ll": [28.0395, -81.9498], "state": "FL",
     "aliases": ["lakeland", "polk county"]},
    {"name": "Ocala, FL",               "ll": [29.1872, -82.1401], "state": "FL",
     "aliases": ["ocala", "marion county"]},
    {"name": "Daytona Beach, FL",       "ll": [29.2108, -81.0228], "state": "FL",
     "aliases": ["daytona", "volusia"]},
    {"name": "Tallahassee, FL",         "ll": [30.4383, -84.2807], "state": "FL",
     "aliases": ["tallahassee", "leon county"]},
    {"name": "Pensacola, FL",           "ll": [30.4213, -87.2169], "state": "FL",
     "aliases": ["pensacola", "escambia"]},
    {"name": "Gainesville, FL",         "ll": [29.6516, -82.3248], "state": "FL",
     "aliases": ["gainesville, fl", "alachua"]},
    {"name": "Lexington-Fayette, KY",   "ll": [38.0406, -84.5037], "state": "KY",
     "aliases": ["lexington", "fayette"]},
    {"name": "Bowling Green, KY",       "ll": [36.9685, -86.4808], "state": "KY",
     "aliases": ["bowling green", "warren county"]},

    # ===== Hidden gem markets =====
    {"name": "Tupelo, MS",              "ll": [34.2576, -88.7034], "state": "MS",
     "aliases": ["tupelo", "lee county, ms"]},
    {"name": "Hattiesburg, MS",         "ll": [31.3271, -89.2903], "state": "MS",
     "aliases": ["hattiesburg", "forrest county"]},
    {"name": "Oxford, MS",              "ll": [34.3665, -89.5187], "state": "MS",
     "aliases": ["oxford, ms", "lafayette county"]},
    {"name": "Auburn-Opelika, AL",      "ll": [32.6099, -85.4808], "state": "AL",
     "aliases": ["auburn", "opelika", "lee county, al"]},
    {"name": "The Shoals (Florence-Muscle Shoals), AL", "ll": [34.7998, -87.6773], "state": "AL",
     "aliases": ["the shoals", "florence-muscle shoals", "florence, al", "muscle shoals", "lauderdale", "colbert"]},
    {"name": "Cullman, AL",             "ll": [34.1748, -86.8434], "state": "AL",
     "aliases": ["cullman"]},
    {"name": "Dothan, AL",              "ll": [31.2232, -85.3905], "state": "AL",
     "aliases": ["dothan", "houston"]},
    {"name": "Statesboro, GA",          "ll": [32.4499, -81.7832], "state": "GA",
     "aliases": ["statesboro", "bulloch"]},
    {"name": "Brunswick, GA",           "ll": [31.1500, -81.4915], "state": "GA",
     "aliases": ["brunswick / glynn", "glynn county", "brunswick, ga"]},
    {"name": "Valdosta, GA",            "ll": [30.8327, -83.2785], "state": "GA",
     "aliases": ["valdosta", "lowndes"]},
    {"name": "Aiken, SC",               "ll": [33.5604, -81.7196], "state": "SC",
     "aliases": ["aiken", "north augusta"]},
    {"name": "Sumter, SC",              "ll": [33.9204, -80.3414], "state": "SC",
     "aliases": ["sumter"]},
    {"name": "Florence, SC",            "ll": [34.1954, -79.7626], "state": "SC",
     "aliases": ["florence, sc", "florence county"]},
    {"name": "Hickory, NC",             "ll": [35.7335, -81.3445], "state": "NC",
     "aliases": ["hickory", "catawba"]},
    {"name": "Greenville, NC",          "ll": [35.6127, -77.3664], "state": "NC",
     "aliases": ["greenville, nc", "pitt"]},
    {"name": "Boone, NC",               "ll": [36.2168, -81.6746], "state": "NC",
     "aliases": ["boone", "watauga"]},
    {"name": "Crestview / Niceville / Fort Walton Beach, FL", "ll": [30.7621, -86.5707], "state": "FL",
     "aliases": ["crestview", "niceville", "fort walton", "okaloosa"]},
    {"name": "Panama City, FL",         "ll": [30.1588, -85.6602], "state": "FL",
     "aliases": ["panama city", "bay county"]},
    {"name": "Lake City, FL",           "ll": [30.1894, -82.6393], "state": "FL",
     "aliases": ["lake city", "columbia county"]},
    {"name": "Elizabethtown / Glendale, KY", "ll": [37.6940, -85.8591], "state": "KY",
     "aliases": ["elizabethtown", "glendale", "hardin county"]},
    {"name": "Owensboro, KY",           "ll": [37.7742, -87.1133], "state": "KY",
     "aliases": ["owensboro", "daviess"]},
    {"name": "Paducah, KY",             "ll": [37.0834, -88.6000], "state": "KY",
     "aliases": ["paducah"]},
    {"name": "Richmond / Berea, KY",    "ll": [37.7479, -84.2947], "state": "KY",
     "aliases": ["richmond, ky", "berea", "madison county, ky"]},
    {"name": "Murray, KY",              "ll": [36.6103, -88.3148], "state": "KY",
     "aliases": ["murray", "calloway"]},

    # ===== Out-of-focus but in-whitelist (for parcels that have appeared) =====
    {"name": "Bryan County, GA",        "ll": [32.0335, -81.4271], "state": "GA",
     "aliases": ["bryan county", "richmond hill", "pembroke"]},
    {"name": "Pooler, GA",              "ll": [32.1156, -81.2466], "state": "GA",
     "aliases": ["pooler"]},
    {"name": "Port Wentworth, GA",      "ll": [32.1490, -81.1659], "state": "GA",
     "aliases": ["port wentworth"]},
    {"name": "Jacksonville, FL",        "ll": [30.3322, -81.6557], "state": "FL",
     "aliases": ["jacksonville", "duval", "clay county"]},
    {"name": "Trussville, AL",          "ll": [33.6201, -86.6089], "state": "AL",
     "aliases": ["trussville"]},
    {"name": "Decatur, AL",             "ll": [34.6059, -86.9833], "state": "AL",
     "aliases": ["decatur, al", "morgan county"]},
    {"name": "Tuscaloosa, AL",          "ll": [33.2098, -87.5692], "state": "AL",
     "aliases": ["tuscaloosa"]},
    {"name": "Birmingham, AL",          "ll": [33.5186, -86.8104], "state": "AL",
     "aliases": ["birmingham"]},
    {"name": "Murfreesboro, TN",        "ll": [35.8456, -86.3903], "state": "TN",
     "aliases": ["murfreesboro"]},
    {"name": "Huntsville-Madison, AL",  "ll": [34.7304, -86.5861], "state": "AL",
     "aliases": ["huntsville", "madison county, al"]},
    {"name": "Conway / Myrtle Beach, SC", "ll": [33.6891, -78.8867], "state": "SC",
     "aliases": ["conway", "myrtle beach", "horry"]},
]

# State centroids — used as a fallback when a parcel's market doesn't match any known city
STATE_CENTROIDS = {
    "FL": [27.9944, -81.7603],
    "GA": [32.6415, -83.4426],
    "SC": [33.8569, -80.9450],
    "NC": [35.5557, -79.3877],
    "TN": [35.8580, -86.3505],
    "AL": [32.7794, -86.8287],
    "KY": [37.6681, -84.6701],
    "MS": [32.7416, -89.6787],
}

# Pretty groupings for the Manual Search tab dropdown
GROUPS = [
    ("Primary — Sun Belt & Carolinas", [
        "Charleston, SC", "Wilmington, NC", "Greenville-Spartanburg, SC",
        "Knoxville, TN", "Chattanooga, TN", "Asheville, NC", "Savannah, GA",
        "Augusta, GA", "Columbia, SC",
    ]),
    ("Primary — Florida", [
        "Lakeland, FL", "Ocala, FL", "Daytona Beach, FL", "Tallahassee, FL",
        "Pensacola, FL", "Gainesville, FL",
    ]),
    ("Primary — Kentucky", [
        "Lexington-Fayette, KY", "Bowling Green, KY",
    ]),
    ("Hidden Gem — Mississippi", [
        "Tupelo, MS", "Hattiesburg, MS", "Oxford, MS",
    ]),
    ("Hidden Gem — Alabama", [
        "Auburn-Opelika, AL", "The Shoals (Florence-Muscle Shoals), AL",
        "Cullman, AL", "Dothan, AL",
    ]),
    ("Hidden Gem — Georgia", [
        "Statesboro, GA", "Brunswick, GA", "Valdosta, GA",
    ]),
    ("Hidden Gem — Carolinas", [
        "Aiken, SC", "Sumter, SC", "Florence, SC",
        "Hickory, NC", "Greenville, NC", "Boone, NC",
    ]),
    ("Hidden Gem — Florida", [
        "Crestview / Niceville / Fort Walton Beach, FL",
        "Panama City, FL", "Lake City, FL",
    ]),
    ("Hidden Gem — Kentucky", [
        "Elizabethtown / Glendale, KY", "Owensboro, KY", "Paducah, KY",
        "Richmond / Berea, KY", "Murray, KY",
    ]),
]


def find_market(market_str):
    """Match a parcel's market string to a known market via aliases.
    Returns the market dict or None."""
    if not market_str:
        return None
    m = market_str.lower()
    for market in MARKETS:
        for alias in market["aliases"]:
            if alias in m:
                return market
    return None


def fallback_state(market_str):
    """Try to guess the 2-letter state from the parcel's market string."""
    if not market_str:
        return None
    m = market_str.upper()
    for code in STATE_CENTROIDS:
        # Match patterns like ", FL " or ", FL (" or ", FL)" or " FL "
        if f", {code}" in m or f" {code} " in m or m.endswith(f", {code}"):
            return code
    return None
