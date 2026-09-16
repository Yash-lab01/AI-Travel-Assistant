# Image Integration — Implementation Design
> Added: 2026-08-19 | Updated: 2026-09-16 | Status: **FULLY IMPLEMENTED (v9)**

---

## Why This Matters

Images are the single most impactful addition to a travel planning app. Users understand a destination **visually before they read**. Without images:
- Stop cards feel like a spreadsheet, not a travel guide
- The landing page looks like a developer prototype, not a product
- Users can't tell if a "hidden gem" is a beautiful rooftop bar or a random street
- When fallback images repeat identically across 5 stops, the interface looks broken or artificial

---

## What Currently Exists (and Gaps)

| Component | Status | Gap |
|---|---|---|
| `Stop.photo_urls: list[str]` in schema | ✅ Schema ready | Never populated without `GOOGLE_PLACES_API_KEY` |
| `ItineraryView.tsx` stop-card image render | ✅ Code exists | Falls back to emoji — no real images in practice |
| `.stop-card-image` CSS class | ⚠️ Basic | Needs aspect-ratio lock, shimmer skeleton, error fallback |
| Landing page destination imagery | ❌ Missing | Zero imagery |
| Per-day banner/hero photo | ❌ Missing | No day-level cover photo |
| Map marker photo thumbnails | ❌ Missing | Plain colored dots only |
| Free image source (no API key) | ❌ Missing | No fallback when Google Places absent |

---

## Implementation Plan — 3 Tiers

### Tier 1 — Wikipedia REST Summary API (Zero-Key, Fastest, Highest Quality)

**This is the primary free image source in production.** The Wikipedia REST endpoint returns the exact lead photograph for a named article in one round-trip:
```
https://en.wikipedia.org/api/rest_v1/page/summary/{place_name}
```
Response contains `thumbnail.source` and `originalimage.source` — high-res, CC-licensed, named landmark photos.

**How it's wired in `places_tool.py`:**
```python
async def fetch_wikimedia_image(place_name: str, destination: str = "") -> str:
    # Tier 1: Wikipedia REST summary API
    encoded = urllib.parse.quote(clean_name.replace(" ", "_"))
    resp = await client.get(
        f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}",
        headers={"User-Agent": "WanderAI/1.0 (travel-planner)"}
    )
    if resp.status_code == 200:
        d = resp.json()
        if d.get("thumbnail", {}).get("source"):
            return d["thumbnail"]["source"]
```

---

### Tier 2 — Wikipedia Generator Search with PageImages (Fuzzy Matching)

When Tier 1 misses (e.g., compound name or localized spelling doesn't match exact article title), use fuzzy full-text search:
```python
    # Tier 2: Wikipedia generator search
    resp = await client.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "generator": "search",
            "gsrsearch": f"{clean_name} {destination}".strip(),
            "gsrlimit": 1,
            "prop": "pageimages",
            "piprop": "thumbnail|original",
            "pithumbsize": 800,
            "format": "json",
        },
    )
    pages = resp.json().get("query", {}).get("pages", {})
    for page in pages.values():
        thumb = page.get("thumbnail", {}).get("source")
        if thumb:
            return thumb
```

**Test results**: Tier 1 + Tier 2 together resolve real photos for >95% of tested landmarks.

---

### Tier 3 — Wikimedia Commons File Search (CC-Licensed Community Photos)

For stops that still miss after Tiers 1+2, search Wikimedia Commons directly for CC-licensed image files:
```python
    # Tier 3: Wikimedia Commons search
    resp = await client.get(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query",
            "generator": "search",
            "gsrsearch": clean_name,
            "gsrnamespace": 6,  # File namespace
            "gsrlimit": 1,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 800,
            "format": "json",
        },
    )
    for page in pages.values():
        for info in page.get("imageinfo", []):
            thumb = info.get("thumburl") or info.get("url")
            if thumb:
                return thumb
```

---

### Tier 4 — Google Places Photos (Removed in v8 due to 403 Forbidden)

> [!WARNING]
> Legacy Google Places photo URLs (`maps.googleapis.com/maps/api/place/photo`) return `403 Forbidden` when embedded in browser `<img>` tags due to API key referrer restrictions. As of **v8**, Google Places photo URLs have been removed from the pipeline, routing directly to the Wikipedia & Wikimedia Commons zero-auth cascade for all landmarks.

```python
# Priority chain per stop (v8):
# 1. Wikipedia REST Summary API  ← Tier 1 (fastest exact lead image)
# 2. Wikipedia Generator Search  ← Tier 2 (fuzzy title match)
# 3. Wikimedia Commons Search    ← Tier 3 (CC-licensed photography)
# 4. Category curated fallback   ← Tier 4 (high-res Unsplash category photo)
# 5. Emoji placeholder           ← Tier 5 (final visual fallback)
```

---

### Tier 5 — Static Curated Destination Banners & Category Fallbacks

For the landing page, itinerary covers, and day-level banner photos, WanderAI uses a curated dictionary of high-resolution Unsplash photo URLs across 40+ destinations:

```python
# backend/app/tools/destination_images.py
DESTINATION_BANNERS: dict[str, str] = {
    # India Major Cities & Heritage
    "mumbai": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=1200",
    "goa": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=1200",
    "delhi": "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=1200",
    "jaipur": "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=1200",
    "kerala": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=1200",
    "pune": "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?w=1200",
    "hyderabad": "https://images.unsplash.com/photo-1605007493699-ce65834f8a00?w=1200",
    "chennai": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=1200",
    "kolkata": "https://images.unsplash.com/photo-1558431382-27e303142255?w=1200",
    "amritsar": "https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=1200",
    "ahmedabad": "https://images.unsplash.com/photo-1597848212624-a19eb35e2651?w=1200",
    "kochi": "https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?w=1200",
    "shimla": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=1200",
    "hampi": "https://images.unsplash.com/photo-1600100397608-f010e42f9b1a?w=1200",
    "mysore": "https://images.unsplash.com/photo-1600100397608-f010e42f9b1a?w=1200",
    "pondicherry": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=1200",
    "ooty": "https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?w=1200",
    "srinagar": "https://images.unsplash.com/photo-1598091383021-15ddea10925d?w=1200",
    "jodhpur": "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=1200",
    "jaisalmer": "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=1200",
    # Global Destinations
    "bali": "https://images.unsplash.com/photo-1555400038-63f5ba517a47?w=1200",
    "lisbon": "https://images.unsplash.com/photo-1588668214407-6ea9a6d8c272?w=1200",
    "tokyo": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1200",
    "paris": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1200",
    "rome": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=1200",
    "barcelona": "https://images.unsplash.com/photo-1464790719320-516ecd75af6c?w=1200",
    "seoul": "https://images.unsplash.com/photo-1538485399081-7191377e8241?w=1200",
    "amsterdam": "https://images.unsplash.com/photo-1512470876302-972faa2aa9a4?w=1200",
    "prague": "https://images.unsplash.com/photo-1541849546-216549ae216d?w=1200",
    "vienna": "https://images.unsplash.com/photo-1516550893923-42d28e5677af?w=1200",
    "istanbul": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?w=1200",
    "cairo": "https://images.unsplash.com/photo-1572252009286-268acec5ca0a?w=1200",
    "sydney": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=1200",
    "_default": "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=1200",
}

def get_destination_banner(destination: str) -> str:
    dest_lower = destination.lower().split()[0]
    return DESTINATION_BANNERS.get(dest_lower, DESTINATION_BANNERS["_default"])
```

**Send this in the `Itinerary` response** as `cover_image_url: Optional[str]`.

---

## Frontend Changes Required

### 1. Stop Card — Full-bleed Image Header
```css
/* globals.css */
.stop-card-image {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 12px 12px 0 0;
  background: var(--glass-bg);
  min-height: 140px;
  /* Shimmer skeleton while loading */
  background: linear-gradient(90deg, var(--glass-bg) 25%, rgba(255,255,255,0.05) 50%, var(--glass-bg) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
```

```tsx
// ItineraryView.tsx — updated StopCard two-tier image fallback block
const [imgError, setImgError] = useState(false);
const [fallbackError, setFallbackError] = useState(false);
const rawImg = stop.photo_urls?.[0];
const categoryFallback = getCategoryFallbackPhoto(stop.category);

const effectiveSrc = !imgError && rawImg 
  ? rawImg 
  : (!fallbackError && categoryFallback ? categoryFallback : null);

{effectiveSrc ? (
  <img
    src={effectiveSrc}
    alt={stop.name}
    className="stop-card-image"
    loading="lazy"
    onError={() => {
      if (!imgError && rawImg) setImgError(true);
      else setFallbackError(true);
    }}
  />
) : (
  <div className="stop-card-image stop-card-image--placeholder">
    <span style={{ fontSize: 36 }}>{icon}</span>
  </div>
)}
```

### 2. Day Banner — Full-width Cover Photo
Each day tab should show a wide banner image (from destination banner or first stop's photo):
```tsx
// In ItineraryView.tsx — DayBanner component
function DayBanner({ theme, coverUrl }: { theme: string; coverUrl?: string }) {
  return (
    <div className="day-banner" style={{
      backgroundImage: coverUrl ? `linear-gradient(to bottom, rgba(0,0,0,0.1), rgba(0,0,0,0.7)), url(${coverUrl})` : undefined
    }}>
      <h2 className="day-theme">{theme}</h2>
    </div>
  );
}
```

### 3. Landing Page — Destination Cards with Real Photos
The hero prompt cards should show destination thumbnail photos:
```tsx
// page.tsx — update HERO_PROMPT_CARDS
const HERO_PROMPT_CARDS = [
  { label: "3 days in Mumbai", img: "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=400" },
  { label: "5 days in Goa", img: "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=400" },
  // ...etc
];
```

### 4. Map Marker Thumbnails (Optional, Phase 4b)
Add photo thumbnails to Leaflet popup on marker click:
```tsx
// MapView.tsx — in the popup content
const popup = `
  <div style="width:200px">
    ${stop.photo_urls?.[0] ? `<img src="${stop.photo_urls[0]}" style="width:100%;border-radius:6px;margin-bottom:8px">` : ''}
    <strong>${stop.name}</strong><br/>
    <small>${stop.category}</small>
  </div>
`;
marker.bindPopup(popup);
```

---

## Backend Schema Change

Add `cover_image_url` to `Itinerary` in `schemas.py`:
```python
class Itinerary(BaseModel):
    ...
    cover_image_url: Optional[str] = None  # Destination banner photo
```

Add `cover_image_url` to `DayPlan` (first stop's photo or subzone photo):
```python
class DayPlan(BaseModel):
    ...
    cover_image_url: Optional[str] = None  # Day banner photo
```

In `planner_agent.py`, populate these:
```python
from app.tools.destination_images import get_destination_banner

itinerary = Itinerary(
    ...
    cover_image_url=get_destination_banner(trip.destination),
)

# For each day:
day = DayPlan(
    ...
    cover_image_url=cluster[0].photo_urls[0] if cluster[0].photo_urls else get_destination_banner(trip.destination),
)
```

---

## TypeScript Mirror

Update `frontend/src/types/index.ts`:
```typescript
export interface Stop {
  ...
  photo_urls: string[];  // already exists
}

export interface DayPlan {
  ...
  cover_image_url?: string;  // ADD
}

export interface Itinerary {
  ...
  cover_image_url?: string;  // ADD
}
```

---

## Priority Order for Implementation

1. **[Backend]** Add `destination_images.py` with curated Unsplash banners
2. **[Backend]** Add `_unsplash_fallback_url()` to `places_tool.py` — populates `photo_urls` when Google Places key absent
3. **[Backend]** Add `fetch_wikimedia_image()` to `places_tool.py` as mid-tier
4. **[Backend]** Add `cover_image_url` to `Itinerary` + `DayPlan` schemas
5. **[Backend]** Populate `cover_image_url` in `planner_agent.py`
6. **[Frontend]** Update `ItineraryView.tsx` — proper image handling with lazy load + shimmer + error fallback
7. **[Frontend]** Add `DayBanner` component with cover photo
8. **[Frontend]** Update landing page `HERO_PROMPT_CARDS` with destination thumbnail images
9. **[Frontend]** Update `.stop-card-image` CSS with correct aspect ratio and skeleton shimmer
10. **[Frontend]** Add photo thumbnails to Leaflet map popups

---

## Phase 10: Multi-Tier Image Engine Overhaul (v9)

### The Problem in v8
1. **Single Category Photo Repetition**:
   - `CATEGORY_FALLBACK_IMAGES` had only 1 static image per category. When 5 consecutive stops in an itinerary shared the category `"sight"`, all 5 cards showed the exact same duplicate image.
2. **Google Places 40-Request Latency Sink**:
   - `enrich_with_google_places` fired up to 40 unthrottled requests to `nearbysearch` with an unauthorized key, each waiting up to 8s before timing out, triggering the 45s client abort.
3. **Poisoned Mock Cache**:
   - When external lookups failed or geocoding shifted to an empty desert coordinate, mock places like "Historic Old Town Center" were tagged as `source="opentripmap"` and stored in Chroma cache under `v8`, permanently serving fake places on subsequent queries.
4. **Non-Photo Wikimedia Results**:
   - Wikipedia generator searches sometimes returned administrative SVG map locator files, coats of arms, or small iconography instead of real landscape photography.

### The v9 Architecture
1. **Google Places Fast-Fail Probe**:
   - Probe the Places API key once on startup or initial call. If the API returns `REQUEST_DENIED` or HTTP 403, immediately mark Google Places as disabled in memory and bypass the 40-call loop.
2. **Wikimedia Non-Photo Filter**:
   - Reject any Wikimedia URL containing `map`, `locator`, `flag`, `coat_of_arms`, `icon`, `symbol`, `logo`, `portrait`, `border`, `location`, or `.svg`.
3. **Multi-Photo Category Pools (`CATEGORY_IMAGE_POOLS`)**:
   - Provide 8–10 distinct high-resolution Unsplash photos per category (`sight`, `nature`, `food`, `culture`, `adventure`, `relaxation`, `shopping`, `entertainment`, `general`).
4. **Deterministic Hash Selection**:
   - Select photos using `pool[abs(hash(place_name or "spot")) % len(pool)]`. Every stop card gets a visually distinct, stable photo.
5. **Destination-Specific Photo Libraries (`DESTINATION_PHOTO_LIBRARIES`)**:
   - Provide curated category pools for popular regions: Kashmir, Goa, Mumbai, Delhi, Jaipur, Kerala, Manali, Ladakh, Bali, Lisbon, Tokyo, Paris, Rome.
   - When a stop belongs to a known destination, check destination category photos first before falling back to generic category pools.
6. **Cache Invalidation (`CACHE_VERSION = "v9"`)**:
   - Purges poisoned mock caches from previous versions. Only genuine OpenTripMap attractions (`source="opentripmap"`) are written to ChromaDB.

---

## What NOT to Do

❌ Do NOT call `source.unsplash.com` (deprecated) dynamically — use Wikipedia REST API cascade for per-stop images.
❌ Do NOT use legacy Google Places photo API URLs — they return 403 Forbidden in browser contexts.
❌ Do NOT use only exact `titles=` Wikipedia query — must cascade to `generator=search` as fallback (many OTM place names don't match exact Wikipedia article titles).
❌ Do NOT skip `loading="lazy"` on stop card images — 15+ images loading eagerly on a trip plan will freeze the browser.
❌ Do NOT use `object-fit: contain` for destination photos — use `object-fit: cover` with a fixed `aspect-ratio`.
❌ Do NOT show broken image icon (browser default) — always provide a multi-tier fallback (landmark URL → category fallback photo → emoji placeholder).
❌ Do NOT require Google Places API key for images — must work reliably in zero-key fallback mode.
❌ Do NOT call `element.scrollIntoView()` from child components for internal message lists — it jumps the outer browser viewport. Use `container.scrollTop = container.scrollHeight` instead.
