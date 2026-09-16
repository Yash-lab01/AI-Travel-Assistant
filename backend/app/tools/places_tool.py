"""
OpenTripMap + Google Places tool — Phase 3
Fetches real tourist attractions for a destination, enriches with Google Places.
Includes regional multi-zone awareness for states/regions (Goa, Rajasthan, Bali, Mumbai, Pune, Delhi, Kerala, etc.)
so multi-day trips explore geographically distinct zones instead of a 6km micro-cluster.

Tier 1: OpenTripMap (free, 1000 req/day) — primary attraction data
Tier 2: Google Places API — enrichment: photos, ratings, review_count, hours

Caches results in Chroma to avoid re-fetching on repeat queries.
"""
import httpx
import asyncio
import os
import hashlib
import json
import uuid
from typing import Optional
from app.models.schemas import Stop, TravelStyle
from app.vector_store.chroma_client import get_chroma_client
from app.tools.destination_images import get_destination_banner, get_category_fallback_image

# ── Config ────────────────────────────────────────────────────────────────────
OTM_BASE = "https://api.opentripmap.com/0.1/en/places"
OTM_KEY   = os.getenv("OPENTRIPMAP_API_KEY", "")
GPLACES_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

# Increment this when the parser or data schema changes to auto-invalidate Chroma cache
CACHE_VERSION = "v9"

# OTM category groups by travel style preference
CATEGORY_MAP = {
    "attraction":   "historic,cultural,natural",
    "food":         "foods",
    "nature":       "natural",
    "nightlife":    "adult,amusements",
    "shopping":     "shops",
    "viewpoint":    "natural,interesting_places",
}

ALL_KINDS = "historic,cultural,natural,foods,interesting_places,architecture"

# ── Regional Sub-Zone Centroids for Multi-Day Geographic Dispersion ─────────
REGIONAL_SUBZONES: dict[str, list[dict]] = {
    "kashmir": [
        {"name": "Srinagar (Dal Lake, Mughal Gardens & Downtown)", "lat": 34.0837, "lon": 74.7973},
        {"name": "Gulmarg (Apharwat Peak, Gondola & Pine Valleys)", "lat": 34.0484, "lon": 74.3805},
        {"name": "Pahalgam (Betaab Valley, Aru & Lidder River)",    "lat": 34.0156, "lon": 75.3188},
        {"name": "Sonamarg (Thajiwas Glacier & Mountain Passes)",  "lat": 34.3000, "lon": 75.2900},
    ],
    "himachal": [
        {"name": "Manali (Old Manali, Solang Valley & Hadimba)",    "lat": 32.2396, "lon": 77.1887},
        {"name": "Naggar & Kullu Valley (Castles & Art Galleries)", "lat": 32.1465, "lon": 77.1706},
        {"name": "Kasol & Parvati Valley (Pine Treks & Cafes)",     "lat": 32.0100, "lon": 77.3150},
    ],
    "ladakh": [
        {"name": "Leh Central (Leh Palace, Shanti Stupa & Market)", "lat": 34.1526, "lon": 77.5771},
        {"name": "Indus Valley Monasteries (Thiksey & Hemis)",      "lat": 34.0575, "lon": 77.6669},
        {"name": "Nubra Valley & Hunder Sand Dunes",               "lat": 34.5760, "lon": 77.4280},
    ],
    "goa": [
        {"name": "North Goa (Calangute, Anjuna & Coastal Forts)", "lat": 15.58, "lon": 73.76},
        {"name": "Central Goa (Panjim, Fontainhas & Old Goa)",   "lat": 15.50, "lon": 73.83},
        {"name": "South Goa (Colva, Cabo de Rama & Palolem)",    "lat": 15.05, "lon": 73.96},
    ],
    "mumbai": [
        {"name": "South Mumbai (Colaba, Fort & Marine Drive)",   "lat": 18.922, "lon": 72.834},
        {"name": "Central Mumbai (Bandra Fort & Seaside Promenades)", "lat": 19.055, "lon": 72.829},
        {"name": "North Mumbai (Juhu Beach & Cultural Heritage)", "lat": 19.102, "lon": 72.827},
    ],
    "pune": [
        {"name": "Central Heritage (Shaniwarwada & Old Peths)",  "lat": 18.519, "lon": 73.855},
        {"name": "Shivajinagar & Deccan (Caves & Hill Views)",   "lat": 18.531, "lon": 73.844},
        {"name": "Camp & Koregaon Park (Palaces & Cafes)",       "lat": 18.548, "lon": 73.901},
        {"name": "Sinhagad Foothills & Waterfalls",              "lat": 18.366, "lon": 73.755},
    ],
    "delhi": [
        {"name": "Old Delhi (Red Fort, Jama Masjid & Bazaars)",  "lat": 28.656, "lon": 77.231},
        {"name": "Central Delhi (India Gate & Imperial Gardens)","lat": 28.612, "lon": 77.227},
        {"name": "South Delhi (Qutub Minar & Historic Ruins)",   "lat": 28.524, "lon": 77.185},
    ],
    "jaipur": [
        {"name": "Pink City (City Palace, Hawa Mahal & Bazaars)","lat": 26.924, "lon": 75.827},
        {"name": "Amer Fort, Stepwells & Aravalli Hills",        "lat": 26.985, "lon": 75.851},
        {"name": "Nahargarh Heights & Sunset Forts",             "lat": 26.937, "lon": 75.815},
    ],
    "rajasthan": [
        {"name": "Jaipur Old City & Royal Palaces", "lat": 26.92, "lon": 75.82},
        {"name": "Amer Fort, Stepwells & Hills",   "lat": 26.98, "lon": 75.85},
        {"name": "Pushkar Holy Lake & Heritage",   "lat": 26.48, "lon": 74.55},
        {"name": "Jodhpur Blue City & Forts",      "lat": 26.29, "lon": 73.02},
    ],
    "bali": [
        {"name": "Ubud Rainforest & Temples",       "lat": -8.51, "lon": 115.26},
        {"name": "Seminyak & Canggu Coastline",     "lat": -8.65, "lon": 115.14},
        {"name": "Uluwatu Cliffs & South Beaches",  "lat": -8.82, "lon": 115.09},
    ],
    "kerala": [
        {"name": "Kochi & Fort Kochi Heritage",    "lat": 9.96,  "lon": 76.24},
        {"name": "Munnar Tea Hills & Waterfalls",  "lat": 10.08, "lon": 77.06},
        {"name": "Alleppey Backwaters & Lagoons",  "lat": 9.49,  "lon": 76.33},
    ],
    "tokyo": [
        {"name": "Shinjuku & Shibuya Neon Pulse",   "lat": 35.69, "lon": 139.70},
        {"name": "Asakusa & Ueno Historic Temples", "lat": 35.71, "lon": 139.79},
        {"name": "Ginza, Tsukiji & Imperial Gardens","lat": 35.67, "lon": 139.76},
    ],
    "lisbon": [
        {"name": "Alfama & Castelo de São Jorge",   "lat": 38.713, "lon": -9.133},
        {"name": "Baixa & Chiado Cultural Heart",   "lat": 38.711, "lon": -9.140},
        {"name": "Belém Historic Tower & Monasteries", "lat": 38.697, "lon": -9.206},
    ],
}

REGION_CENTROIDS: dict[str, tuple[float, float]] = {
    "kashmir": (34.0837, 74.7973),       # Srinagar / Kashmir Valley
    "srinagar": (34.0837, 74.7973),
    "gulmarg": (34.0484, 74.3805),
    "pahalgam": (34.0156, 75.3188),
    "sonamarg": (34.3000, 75.2900),
    "ladakh": (34.1526, 77.5771),        # Leh / Ladakh
    "leh": (34.1526, 77.5771),
    "manali": (32.2396, 77.1887),
    "himachal": (32.2396, 77.1887),
    "shimla": (31.1048, 77.1734),
    "goa": (15.4989, 73.8278),
    "kerala": (9.9312, 76.2673),
    "rajasthan": (26.9124, 75.7873),
    "jaipur": (26.9124, 75.7873),
    "pune": (18.5204, 73.8567),
    "mumbai": (18.9220, 72.8340),
    "delhi": (28.6139, 77.2090),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "lisbon": (38.7223, -9.1393),
    "kyoto": (35.0116, 135.7681),
    "tokyo": (35.6762, 139.6503),
    "bali": (-8.4095, 115.1889),
    "paris": (48.8566, 2.3522),
    "rome": (41.9028, 12.4964),
}

# ── Geocoding helper ──────────────────────────────────────────────────────────
async def geocode_destination(destination: str) -> tuple[float, float]:
    """Convert destination name -> (lat, lon) with region centroid priority & Nominatim (free)."""
    clean_dest = destination.split("(")[0].strip()
    dest_lower = clean_dest.lower()

    # Fast path for known regions to prevent geocoders from selecting obscure duplicate villages
    for key, coords in REGION_CENTROIDS.items():
        if key in dest_lower:
            return coords

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": clean_dest, "format": "json", "limit": 1}
    headers = {"User-Agent": "WanderAI/1.0 (portfolio project)"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                results = resp.json()
                if results:
                    return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        pass

    return 38.7223, -9.1393


# ── Cache key ─────────────────────────────────────────────────────────────────
def _cache_key(destination: str) -> str:
    return hashlib.md5(destination.lower().strip().encode()).hexdigest()[:12]


# ── OpenTripMap fetch ─────────────────────────────────────────────────────────
async def fetch_otm_places(lat: float, lon: float, radius_m: int = 15000, limit: int = 40) -> list[dict]:
    """Fetch places from OpenTripMap around a lat/lon, properly parsing flat JSON."""
    if not OTM_KEY:
        # Return empty — caller decides whether to use mock data
        return []

    params = {
        "apikey":  OTM_KEY,
        "radius":  radius_m,
        "lon":     lon,
        "lat":     lat,
        "kinds":   ALL_KINDS,
        "format":  "json",
        "limit":   limit,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{OTM_BASE}/radius", params=params)
            if resp.status_code != 200:
                print(f"[places_tool] OTM HTTP {resp.status_code} for ({lat},{lon})")
                return []
            features = resp.json()

        if not isinstance(features, list):
            return []

        places = []
        for f in features:
            if not isinstance(f, dict):
                continue
            xid = f.get("xid") or f.get("properties", {}).get("xid")
            name = f.get("name") or f.get("properties", {}).get("name", "")
            if not xid or not name or len(name.strip()) <= 2:
                continue

            kinds = f.get("kinds") or f.get("properties", {}).get("kinds", "")
            point = f.get("point", {})
            p_lat = point.get("lat")
            p_lon = point.get("lon")

            if p_lat is None or p_lon is None:
                coords = f.get("geometry", {}).get("coordinates", [None, None])
                p_lon = coords[0]
                p_lat = coords[1]

            if p_lat is None or p_lon is None:
                continue

            rate = f.get("rate") or f.get("properties", {}).get("rate", 0)
            places.append({
                "xid":   xid,
                "name":  name.strip(),
                "kinds": kinds,
                "lat":   float(p_lat),
                "lon":   float(p_lon),
                "rate":  rate,
            })

        return places
    except Exception as e:
        print(f"[places_tool] OTM fetch failed: {e}")
        return []



# Module-level Google Places authorization probe status
_GPLACES_STATUS: Optional[bool] = None

# ── Google Places enrichment ──────────────────────────────────────────────────
async def enrich_with_google_places(name: str, lat: float, lon: float) -> dict:
    """
    Returns: {photo_url, rating, review_count, place_id}
    Falls back gracefully if no API key, unauthorized, or no result.
    Probes key once; if unauthorized, sets _GPLACES_STATUS = False and bypasses loop.
    """
    global _GPLACES_STATUS
    if not GPLACES_KEY or _GPLACES_STATUS is False:
        return {}

    try:
        search_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        async with httpx.AsyncClient(timeout=4) as client:
            resp = await client.get(search_url, params={
                "key":      GPLACES_KEY,
                "location": f"{lat},{lon}",
                "radius":   300,
                "keyword":  name,
            })
            if resp.status_code != 200:
                _GPLACES_STATUS = False
                return {}

            data = resp.json()
            status = data.get("status", "")
            if status in ("REQUEST_DENIED", "OVER_QUERY_LIMIT", "INVALID_REQUEST"):
                _GPLACES_STATUS = False
                return {}

            _GPLACES_STATUS = True

        if not data.get("results"):
            return {}

        place = data["results"][0]
        place_id = place.get("place_id", "")
        rating   = place.get("rating")
        n_reviews = place.get("user_ratings_total", 0)

        # Note: legacy Google Places photo endpoint returns 403 unless Places API (New) is enabled.
        # We rely on Wikipedia / Wikimedia Commons and curated photography for reliable zero-auth image delivery.
        return {
            "place_id":     place_id,
            "rating":       rating,
            "review_count": n_reviews,
            "photo_url":    "",
        }

    except Exception:
        return {}


# Keywords that indicate SVG maps, coat of arms, flags, or icons rather than real photographs
DISALLOWED_IMAGE_KEYWORDS = (
    ".svg", "map", "locator", "flag", "coat_of_arms", "icon",
    "symbol", "logo", "portrait", "border", "location", "plan",
    "diagram", "chart", "schema", "stamp"
)

def _is_valid_photo_url(url: str) -> bool:
    if not url:
        return False
    lower = url.lower()
    return not any(kw in lower for kw in DISALLOWED_IMAGE_KEYWORDS)

# ── Free Wikipedia & Wikimedia Commons image scraper (Zero-Key / Free Tier) ──
async def fetch_wikimedia_image(place_name: str, destination: str = "") -> str:
    """
    Fetch a real, high-quality photograph from Wikipedia, Wikivoyage & Wikimedia Commons.
    Cascade:
    1. Wikipedia REST summary API (returns exact lead photo for known article slugs)
    2. Wikipedia OpenSearch API (resolves fuzzy search query to canonical article title -> lead photo)
    3. Wikipedia Generator Search with PageImages (fuzzy keyword matching)
    4. Wikimedia Commons Image Search (CC-licensed community photography)
    5. Wikivoyage Travel Search (tourism listings & destination photography)
    Zero auth / completely free endpoints.
    """
    if not place_name or len(place_name.strip()) < 2:
        return ""

    import urllib.parse
    clean_name = place_name.split("(")[0].strip()
    headers = {"User-Agent": "WanderAI/1.0 (travel-planner; contact: support@wanderai.local)"}

    async with httpx.AsyncClient(timeout=6, follow_redirects=True, headers=headers) as client:
        # 1. Try Wikipedia REST summary API (fast & exact article name)
        try:
            encoded = urllib.parse.quote(clean_name.replace(" ", "_"))
            resp = await client.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}")
            if resp.status_code == 200:
                d = resp.json()
                thumb = d.get("thumbnail", {}).get("source") or d.get("originalimage", {}).get("source")
                if thumb and _is_valid_photo_url(thumb):
                    return thumb
        except Exception:
            pass

        # 2. Try Wikipedia OpenSearch to find canonical title, then retrieve its lead photo
        try:
            search_query = f"{clean_name} {destination}".strip() if destination else clean_name
            resp = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "opensearch",
                    "search": search_query,
                    "limit": 3,
                    "namespace": 0,
                    "format": "json",
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 1 and data[1]:
                    for title in data[1]:
                        encoded_title = urllib.parse.quote(title.replace(" ", "_"))
                        s_resp = await client.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}")
                        if s_resp.status_code == 200:
                            sd = s_resp.json()
                            thumb = sd.get("thumbnail", {}).get("source") or sd.get("originalimage", {}).get("source")
                            if thumb and _is_valid_photo_url(thumb):
                                return thumb
        except Exception:
            pass

        # 3. Try Wikipedia Generator Search with PageImages
        try:
            search_query = f"{clean_name} {destination}".strip() if destination else clean_name
            resp = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": search_query,
                    "gsrlimit": 3,
                    "prop": "pageimages",
                    "piprop": "thumbnail|original",
                    "pithumbsize": 800,
                    "format": "json",
                }
            )
            if resp.status_code == 200:
                pages = resp.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    thumb = page.get("thumbnail", {}).get("source") or page.get("original", {}).get("source")
                    if thumb and _is_valid_photo_url(thumb):
                        return thumb
        except Exception:
            pass

        # 4. Try Wikimedia Commons search
        try:
            resp = await client.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": f"{clean_name} {destination}".strip(),
                    "gsrnamespace": 6,
                    "gsrlimit": 3,
                    "prop": "imageinfo",
                    "iiprop": "url",
                    "iiurlwidth": 800,
                    "format": "json",
                }
            )
            if resp.status_code == 200:
                pages = resp.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    for info in page.get("imageinfo", []):
                        thumb = info.get("thumburl") or info.get("url")
                        if thumb and _is_valid_photo_url(thumb):
                            return thumb
        except Exception:
            pass

    return ""


def _unsplash_fallback_url(name: str, category: str, destination: str) -> str:
    """
    Generate a reliable high-res curated photography URL for stops without live API images.
    """
    return get_category_fallback_image(category, name=name, destination=destination)


# ── Main public function ──────────────────────────────────────────────────────
async def get_places_for_destination(
    destination: str,
    num_days: int = 3,
    travel_style: Optional[str] = None,
) -> list[Stop]:
    """
    Full pipeline with multi-zone spatial dispersion for regional trips:
    1. Check Chroma cache
    2. Check if destination matches a multi-zone region (e.g. Pune, Mumbai, Goa, Rajasthan, Bali)
    3. Query POIs across regional subzones or geocoded centroid
    4. Enrich attractions with Google Places + Wikimedia Commons 3-tier image pipeline
    5. Convert to Stop objects and cache in Chroma
    """
    clean_dest = destination.split("(")[0].strip()
    cache_key = _cache_key(clean_dest)
    chroma = get_chroma_client()

    # 1. Check versioned cache — stale entries (wrong CACHE_VERSION) are skipped entirely
    versioned_key = f"{cache_key}_{CACHE_VERSION}"
    try:
        cached = chroma.get_or_create_collection("itineraries").get(
            where={"cache_key": versioned_key},
            limit=80,
        )
        if cached and cached.get("documents"):
            stops = []
            for doc in cached["documents"]:
                try:
                    data = json.loads(doc)
                    stops.append(Stop(**data))
                except Exception:
                    pass
            # Only accept real OTM stops from cache — reject any mocks
            stops = [s for s in stops if s.source == "opentripmap"]
            if len(stops) >= num_days * 3:
                print(f"[places_tool] Cache hit for {clean_dest} ({len(stops)} stops, {CACHE_VERSION})")
                return stops
    except Exception:
        pass

    # 2. Check for multi-zone subzones
    dest_lower = clean_dest.lower()
    matched_region_key = next((k for k in REGIONAL_SUBZONES if k in dest_lower), None)

    otm_places: list[dict] = []

    if matched_region_key and num_days > 1:
        subzones = REGIONAL_SUBZONES[matched_region_key]
        # Query each subzone concurrently for broad geographical spread
        tasks = [fetch_otm_places(sz["lat"], sz["lon"], radius_m=12000, limit=15) for sz in subzones]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for sub_places in results:
            if isinstance(sub_places, list):
                otm_places.extend(sub_places)
    else:
        # Standard centroid search with adaptive radius
        try:
            lat, lon = await geocode_destination(clean_dest)
        except Exception:
            lat, lon = 18.5204, 73.8567

        adaptive_radius = min(25000, 8000 + (num_days * 3500))
        otm_places = await fetch_otm_places(lat, lon, radius_m=adaptive_radius, limit=min(num_days * 15, 50))

    if not otm_places:
        if not OTM_KEY:
            # No OTM key at all — use rich mock placeholders
            try:
                lat, lon = await geocode_destination(clean_dest)
            except Exception:
                lat, lon = 18.5204, 73.8567
            otm_places = _mock_otm_places(lat, lon)
            print(f"[places_tool] No OTM key — using mock places for {clean_dest}")
        else:
            # OTM key exists but returned 0 results — try wider radius once more
            print(f"[places_tool] OTM returned 0 places for {clean_dest} — retrying with wider radius")
            try:
                lat, lon = await geocode_destination(clean_dest)
                otm_places = await fetch_otm_places(lat, lon, radius_m=30000, limit=50)
            except Exception:
                pass
            if not otm_places:
                # Truly no data — fall back to mocks as last resort
                lat2, lon2 = (lat, lon) if 'lat' in dir() else (18.5204, 73.8567)
                otm_places = _mock_otm_places(lat2, lon2)
                print(f"[places_tool] OTM exhausted — using mock places for {clean_dest}")

    # 3. Deduplicate places by name
    seen_names = set()
    unique_places = []
    for p in otm_places:
        norm = p["name"].strip().lower()
        if norm not in seen_names and len(norm) > 2:
            seen_names.add(norm)
            unique_places.append(p)

    # 4. Enrich all items with Google Places (Tier 1)
    enrich_tasks = [
        enrich_with_google_places(p["name"], p["lat"], p["lon"])
        for p in unique_places
    ]
    enrichments = await asyncio.gather(*enrich_tasks, return_exceptions=True)

    # 5. For items without a Google Places photo, query Wikipedia & Wikimedia Commons cascade (Tier 2)
    wiki_tasks = []
    for i, p in enumerate(unique_places):
        enr = enrichments[i] if i < len(enrichments) and isinstance(enrichments[i], dict) else {}
        if not enr.get("photo_url"):
            wiki_tasks.append((i, fetch_wikimedia_image(p["name"], clean_dest)))

    if wiki_tasks:
        wiki_results = await asyncio.gather(*[t[1] for t in wiki_tasks], return_exceptions=True)
        wiki_map = {}
        for (idx, _), res in zip(wiki_tasks, wiki_results):
            if isinstance(res, str) and res:
                wiki_map[idx] = res
    else:
        wiki_map = {}

    # 6. Convert to Stop objects with guaranteed photo_urls (Tier 1 -> Tier 2 -> Tier 3)
    stops: list[Stop] = []
    for i, p in enumerate(unique_places):
        enrichment = enrichments[i] if i < len(enrichments) and isinstance(enrichments[i], dict) else {}
        category = _infer_category(p.get("kinds", ""))

        # 2-tier reliable image resolution: Wikipedia / Wikimedia -> Curated destination & category photography
        fallback_img = get_category_fallback_image(category, name=p["name"], destination=clean_dest)
        photo_url = wiki_map.get(i) or fallback_img
        photo_urls = [photo_url] if photo_url else [fallback_img]

        source = p.get("source", "opentripmap")
        stop = Stop(
            id=str(uuid.uuid4()),
            name=p["name"],
            category=category,
            description=f"Iconic attraction in {clean_dest}.",
            narration=f"A must-see landmark in {clean_dest}, offering rich history and cultural significance.",
            lat=p["lat"],
            lon=p["lon"],
            duration_minutes=75 if category in ["museum", "attraction"] else 60,
            estimated_cost_usd=_estimate_cost(category),
            photo_urls=photo_urls,
            rating=enrichment.get("rating", 4.5),
            review_count=enrichment.get("review_count", 2500),
            source=source,
            is_niche=False,
            niche_score=None,
        )
        stops.append(stop)

    # 7. Cache stops with versioned key (only real OTM stops)
    otm_stops = [s for s in stops if s.source == "opentripmap"]
    if otm_stops:
        try:
            coll = chroma.get_or_create_collection("itineraries")
            doc_strs = [s.model_dump_json() for s in otm_stops]
            ids = [f"{versioned_key}_{s.id}" for s in otm_stops]
            metadatas = [{"cache_key": versioned_key, "destination": clean_dest} for _ in otm_stops]
            coll.add(documents=doc_strs, ids=ids, metadatas=metadatas)
            print(f"[places_tool] Cached {len(otm_stops)} real OTM stops for {clean_dest} ({CACHE_VERSION})")
        except Exception as ce:
            print(f"[places_tool] Cache write failed: {ce}")

    return stops



def _infer_category(kinds: str) -> str:
    kinds_lower = kinds.lower()
    if "museum" in kinds_lower: return "museum"
    if "food" in kinds_lower or "cafe" in kinds_lower or "restaurant" in kinds_lower: return "restaurant"
    if "viewpoint" in kinds_lower or "natural" in kinds_lower or "view" in kinds_lower: return "viewpoint"
    if "beach" in kinds_lower: return "beach"
    if "shop" in kinds_lower or "market" in kinds_lower or "bazaar" in kinds_lower: return "market"
    if "park" in kinds_lower or "garden" in kinds_lower: return "park"
    if "temple" in kinds_lower or "religion" in kinds_lower or "church" in kinds_lower or "mosque" in kinds_lower: return "attraction"
    return "attraction"


def _estimate_cost(category: str) -> float:
    costs = {
        "museum": 8.0,
        "attraction": 5.0,
        "restaurant": 15.0,
        "cafe": 5.0,
        "viewpoint": 0.0,
        "park": 0.0,
        "beach": 0.0,
        "market": 10.0,
    }
    return costs.get(category, 5.0)


def _mock_otm_places(lat: float, lon: float) -> list[dict]:
    """Rich fallback attractions with spatial spread."""
    return [
        {"xid": "m1", "name": "Historic Old Town Center", "kinds": "historic,architecture", "lat": lat + 0.018, "lon": lon + 0.015, "rate": 3, "source": "mock"},
        {"xid": "m2", "name": "National Heritage Museum", "kinds": "museums", "lat": lat + 0.012, "lon": lon - 0.014, "rate": 3, "source": "mock"},
        {"xid": "m3", "name": "Panoramic City Viewpoint", "kinds": "natural,interesting_places", "lat": lat - 0.022, "lon": lon + 0.018, "rate": 3, "source": "mock"},
        {"xid": "m4", "name": "Artisanal Food & Spice Market", "kinds": "foods,shops", "lat": lat - 0.015, "lon": lon - 0.012, "rate": 3, "source": "mock"},
        {"xid": "m5", "name": "Ancient Fortress & Ramparts", "kinds": "historic", "lat": lat + 0.035, "lon": lon + 0.028, "rate": 3, "source": "mock"},
        {"xid": "m6", "name": "Historic Promenade & Gardens", "kinds": "natural,cultural", "lat": lat - 0.032, "lon": lon - 0.025, "rate": 3, "source": "mock"},
        {"xid": "m7", "name": "Botanical Heritage Garden", "kinds": "gardens,natural", "lat": lat + 0.025, "lon": lon - 0.020, "rate": 3, "source": "mock"},
        {"xid": "m8", "name": "Traditional Arts & Craft Bazaar", "kinds": "shops", "lat": lat - 0.018, "lon": lon + 0.030, "rate": 3, "source": "mock"},
    ]
