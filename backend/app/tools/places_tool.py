"""
OpenTripMap + Google Places tool — Phase 1
Fetches real tourist attractions for a destination, enriches with Google Places.

Tier 1: OpenTripMap (free, 1000 req/day) — primary attraction data
Tier 2: Google Places API — enrichment: photos, ratings, review_count, hours

Caches results in Chroma to avoid re-fetching on repeat queries.
"""
import httpx
import asyncio
import os
import hashlib
import json
from typing import Optional
from app.models.schemas import Stop, TravelStyle
from app.vector_store.chroma_client import get_chroma_client

# ── Config ────────────────────────────────────────────────────────────────────
OTM_BASE = "https://api.opentripmap.com/0.1/en/places"
OTM_KEY   = os.getenv("OPENTRIPMAP_API_KEY", "")
GPLACES_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

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

# ── Geocoding helper ──────────────────────────────────────────────────────────
async def geocode_destination(destination: str) -> tuple[float, float]:
    """Convert destination name → (lat, lon) using Nominatim (free)."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": destination, "format": "json", "limit": 1}
    headers = {"User-Agent": "WanderAI/1.0 (portfolio project)"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        results = resp.json()

    if not results:
        raise ValueError(f"Could not geocode destination: {destination}")

    return float(results[0]["lat"]), float(results[0]["lon"])


# ── Cache key ─────────────────────────────────────────────────────────────────
def _cache_key(destination: str) -> str:
    return hashlib.md5(destination.lower().strip().encode()).hexdigest()[:12]


# ── OpenTripMap fetch ─────────────────────────────────────────────────────────
async def fetch_otm_places(lat: float, lon: float, radius_m: int = 6000, limit: int = 40) -> list[dict]:
    """Fetch places from OpenTripMap around a lat/lon."""
    if not OTM_KEY:
        # Return mock data if no API key
        return _mock_otm_places(lat, lon)

    params = {
        "apikey":  OTM_KEY,
        "radius":  radius_m,
        "lon":     lon,
        "lat":     lat,
        "kinds":   ALL_KINDS,
        "rate":    "3",          # minimum rating 3 stars
        "format":  "json",
        "limit":   limit,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f"{OTM_BASE}/radius", params=params)
        resp.raise_for_status()
        features = resp.json()

    places = []
    for f in features:
        props = f.get("properties", {})
        coords = f.get("geometry", {}).get("coordinates", [None, None])
        if not props.get("xid"):
            continue
        places.append({
            "xid":       props["xid"],
            "name":      props.get("name", "Unknown"),
            "kinds":     props.get("kinds", ""),
            "lat":       coords[1],
            "lon":       coords[0],
            "rate":      props.get("rate", 0),
        })

    return places


async def fetch_otm_details(xid: str) -> dict:
    """Fetch detailed info for a single OTM place."""
    if not OTM_KEY:
        return {}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{OTM_BASE}/xid/{xid}",
            params={"apikey": OTM_KEY},
        )
        if resp.status_code != 200:
            return {}
        return resp.json()


# ── Google Places enrichment ──────────────────────────────────────────────────
async def enrich_with_google_places(name: str, lat: float, lon: float) -> dict:
    """
    Returns: {photo_url, rating, review_count, place_id}
    Falls back gracefully if no API key or no result.
    """
    if not GPLACES_KEY:
        return {}

    try:
        # Step 1: Find nearby matching place
        search_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(search_url, params={
                "key":      GPLACES_KEY,
                "location": f"{lat},{lon}",
                "radius":   200,
                "keyword":  name,
            })
            data = resp.json()

        if not data.get("results"):
            return {}

        place = data["results"][0]
        place_id = place.get("place_id", "")
        rating   = place.get("rating")
        n_reviews = place.get("user_ratings_total", 0)
        photos   = place.get("photos", [])

        photo_url = ""
        if photos and GPLACES_KEY:
            ref = photos[0]["photo_reference"]
            photo_url = (
                f"https://maps.googleapis.com/maps/api/place/photo"
                f"?maxwidth=800&photo_reference={ref}&key={GPLACES_KEY}"
            )

        return {
            "place_id":     place_id,
            "rating":       rating,
            "review_count": n_reviews,
            "photo_url":    photo_url,
        }

    except Exception:
        return {}


# ── Main public function ──────────────────────────────────────────────────────
async def get_places_for_destination(
    destination: str,
    num_days: int = 3,
    travel_style: Optional[str] = None,
) -> list[Stop]:
    """
    Full pipeline:
    1. Check Chroma cache
    2. Geocode destination
    3. Fetch OTM places
    4. Enrich top N with Google Places
    5. Convert to Stop objects
    6. Cache in Chroma

    Returns list of Stop objects (without is_niche scoring — that's Phase 2).
    """
    from app.models.schemas import Stop
    import uuid

    cache_key = _cache_key(destination)
    chroma = get_chroma_client()

    # ── Check cache ───────────────────────────────────────────────────────────
    try:
        cached = chroma.get_collection("itinerary_cache").get(
            where={"destination_key": cache_key},
            limit=50,
        )
        if cached and cached.get("documents"):
            stops = []
            for doc in cached["documents"]:
                try:
                    stops.append(Stop(**json.loads(doc)))
                except Exception:
                    pass
            if stops:
                return stops
    except Exception:
        pass

    # ── Geocode ───────────────────────────────────────────────────────────────
    lat, lon = await geocode_destination(destination)

    # ── Fetch from OTM ────────────────────────────────────────────────────────
    limit = min(num_days * 15, 50)  # ~15 options per day
    raw_places = await fetch_otm_places(lat, lon, limit=limit)

    if not raw_places:
        raw_places = _mock_otm_places(lat, lon)

    # ── Enrich top places with Google ─────────────────────────────────────────
    enrich_limit = min(25, len(raw_places))
    enrich_tasks = [
        enrich_with_google_places(p["name"], p.get("lat", lat), p.get("lon", lon))
        for p in raw_places[:enrich_limit]
    ]
    enrichments = await asyncio.gather(*enrich_tasks, return_exceptions=True)

    # ── Convert to Stop objects ───────────────────────────────────────────────
    stops: list[Stop] = []
    for i, place in enumerate(raw_places):
        enrich = enrichments[i] if i < len(enrichments) and isinstance(enrichments[i], dict) else {}

        category = _kinds_to_category(place.get("kinds", ""))
        photo_urls = [enrich["photo_url"]] if enrich.get("photo_url") else []

        stop = Stop(
            id=str(uuid.uuid4()),
            name=place["name"] or f"Place {i+1}",
            category=category,
            description=f"A {category} in {destination}.",
            lat=place.get("lat") or lat,
            lon=place.get("lon") or lon,
            duration_minutes=_estimate_duration(category),
            estimated_cost_usd=_estimate_cost(category),
            photo_urls=photo_urls,
            rating=enrich.get("rating"),
            review_count=enrich.get("review_count", 0),
            is_niche=False,
            source="opentripmap",
        )
        stops.append(stop)

    # ── Cache result ──────────────────────────────────────────────────────────
    if stops:
        try:
            col = chroma.get_collection("itinerary_cache")
            col.upsert(
                ids=[f"{cache_key}_{i}" for i in range(len(stops))],
                documents=[s.model_dump_json() for s in stops],
                metadatas=[{"destination_key": cache_key, "destination": destination}
                           for _ in stops],
            )
        except Exception:
            pass

    return stops


# ── Helpers ───────────────────────────────────────────────────────────────────
def _kinds_to_category(kinds: str) -> str:
    kinds_lower = kinds.lower()
    if any(k in kinds_lower for k in ["foods", "restaurant", "cafe", "bar"]):
        return "restaurant"
    if any(k in kinds_lower for k in ["museum", "gallery"]):
        return "museum"
    if any(k in kinds_lower for k in ["natural", "park", "garden"]):
        return "park"
    if any(k in kinds_lower for k in ["viewpoint", "panorama"]):
        return "viewpoint"
    if any(k in kinds_lower for k in ["market", "shop"]):
        return "market"
    if any(k in kinds_lower for k in ["beach", "coast"]):
        return "beach"
    return "attraction"


def _estimate_duration(category: str) -> int:
    return {"attraction": 75, "museum": 90, "park": 60, "restaurant": 90,
            "viewpoint": 45, "market": 60, "beach": 120}.get(category, 60)


def _estimate_cost(category: str) -> float:
    return {"attraction": 12.0, "museum": 15.0, "park": 0.0, "restaurant": 25.0,
            "viewpoint": 0.0, "market": 20.0, "beach": 0.0}.get(category, 10.0)


def _mock_otm_places(lat: float, lon: float) -> list[dict]:
    """Returns mock OTM-shaped places for when no API key is set (demo mode)."""
    return [
        {"xid": "m1", "name": "Historic Old Town", "kinds": "historic,architecture", "lat": lat+0.005, "lon": lon+0.003, "rate": 3},
        {"xid": "m2", "name": "Central Market", "kinds": "market,shops",             "lat": lat-0.003, "lon": lon+0.007, "rate": 3},
        {"xid": "m3", "name": "City Viewpoint",  "kinds": "viewpoint,natural",        "lat": lat+0.008, "lon": lon-0.004, "rate": 3},
        {"xid": "m4", "name": "National Museum",  "kinds": "museum,cultural",         "lat": lat-0.006, "lon": lon+0.001, "rate": 3},
        {"xid": "m5", "name": "Riverside Park",   "kinds": "natural,park",            "lat": lat+0.002, "lon": lon-0.009, "rate": 3},
        {"xid": "m6", "name": "Cathedral Square", "kinds": "historic,cultural",       "lat": lat-0.001, "lon": lon+0.005, "rate": 3},
        {"xid": "m7", "name": "Local Food Market","kinds": "foods,market",            "lat": lat+0.004, "lon": lon-0.002, "rate": 3},
        {"xid": "m8", "name": "Art Gallery",      "kinds": "museum,gallery",          "lat": lat-0.007, "lon": lon+0.008, "rate": 3},
        {"xid": "m9", "name": "Harbor Walk",      "kinds": "natural,interesting_places","lat": lat+0.001,"lon": lon-0.006,"rate": 3},
    ]
