# Image Integration — Implementation Design
> Added: 2026-08-19 | Priority: Phase 4 (immediate)

---

## Why This Matters

Images are the single most impactful addition to a travel planning app. Users understand a destination **visually before they read**. Without images:
- Stop cards feel like a spreadsheet, not a travel guide
- The landing page looks like a developer prototype, not a product
- Users can't tell if a "hidden gem" is a beautiful rooftop bar or a random street

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

### Tier 1 — Zero-Key Free Images (MUST implement — works for every user)

**Use Unsplash Source API** (no key required, free):
```
https://source.unsplash.com/800x600/?{keyword}
```
Example: `https://source.unsplash.com/800x600/?mumbai,temple`

**How to wire it in `places_tool.py`:**
```python
def _unsplash_fallback_url(name: str, category: str, destination: str) -> str:
    """Zero-key image from Unsplash Source by keyword."""
    keywords = "+".join(filter(None, [
        name.replace(" ", "+"),
        category if category not in ("attraction", "default") else "",
        destination.split()[0],
    ]))
    return f"https://source.unsplash.com/800x600/?{keywords}"
```

In `get_places_for_destination()`, after building each Stop:
```python
photo_urls = [enrichment["photo_url"]] if enrichment.get("photo_url") else []
if not photo_urls:
    photo_urls = [_unsplash_fallback_url(p["name"], category, clean_dest)]
```

**⚠️ Important Rules for Unsplash Source:**
- Use `source.unsplash.com` (not `api.unsplash.com`) — no key needed
- Always include destination name as a keyword for geographic relevance
- Add `?` + comma-free keywords (use `+` for spaces)
- This URL redirects to a random matching photo on every request — cache the resolved URL, do NOT call it on every render
- Unsplash Source is deprecated; have a secondary fallback to Wikimedia Commons or a static curated map (see Tier 3)

---

### Tier 2 — Google Places Photos (BEST quality, requires key)

Already implemented in `enrich_with_google_places()` — just needs to be called on ALL stops, not just the first `num_days * 5`:

```python
# Current (only enriches top N stops):
enrich_tasks = [
    enrich_with_google_places(p["name"], p["lat"], p["lon"])
    for p in unique_places[:min(len(unique_places), num_days * 5)]  # ← TOO FEW
]

# Fix — enrich all stops (Google Places has generous free tier):
enrich_tasks = [
    enrich_with_google_places(p["name"], p["lat"], p["lon"])
    for p in unique_places  # ← enrich all
]
```

**Also add Wikimedia Commons as a mid-tier:**
```python
async def fetch_wikimedia_image(place_name: str) -> str:
    """Fetch a CC-licensed image from Wikimedia Commons — free, no key."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": place_name,
        "prop": "pageimages",
        "format": "json",
        "pithumbsize": 800,
        "redirects": 1,
    }
    async with httpx.AsyncClient(timeout=8) as client:
        resp = await client.get(url, params=params, headers={"User-Agent": "WanderAI/1.0"})
        pages = resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            thumb = page.get("thumbnail", {})
            if thumb.get("source"):
                return thumb["source"]
    return ""
```

Priority order for `photo_urls[0]`:
1. Google Places photo (if key present + result found)
2. Wikimedia Commons thumbnail (free, CC-licensed, high quality)
3. Unsplash Source fallback (keyword-based, no key)

---

### Tier 3 — Static Curated Destination Banners (for Landing Page + Day Headers)

For the landing page and day-level banner photos, don't hit APIs at all — use a small curated dict of known-good Unsplash photo URLs per destination:

```python
# backend/app/tools/destination_images.py
DESTINATION_BANNERS: dict[str, str] = {
    "mumbai":   "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=1200",
    "goa":      "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=1200",
    "delhi":    "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=1200",
    "jaipur":   "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=1200",
    "kerala":   "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=1200",
    "pune":     "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?w=1200",
    "bali":     "https://images.unsplash.com/photo-1555400038-63f5ba517a47?w=1200",
    "lisbon":   "https://images.unsplash.com/photo-1588668214407-6ea9a6d8c272?w=1200",
    "tokyo":    "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1200",
    "paris":    "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1200",
    "rome":     "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=1200",
    "barcelona":"https://images.unsplash.com/photo-1464790719320-516ecd75af6c?w=1200",
    # fallback for unknown destinations:
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
// ItineraryView.tsx — updated StopCard image block
const [imgError, setImgError] = useState(false);
const imgSrc = stop.photo_urls?.[0];

{imgSrc && !imgError ? (
  <img
    src={imgSrc}
    alt={stop.name}
    className="stop-card-image"
    loading="lazy"
    onError={() => setImgError(true)}
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

## What NOT to Do

❌ Do NOT call `source.unsplash.com` on every React render — it serves a random photo each time (redirect). Cache the URL at generation time in the backend.
❌ Do NOT use Unsplash Source (deprecated) for production — use the static curated dict or Wikimedia for reliability.
❌ Do NOT skip `loading="lazy"` on stop card images — 15+ images loading eagerly on a trip plan will freeze the browser.
❌ Do NOT use `object-fit: contain` for destination photos — use `object-fit: cover` with a fixed `aspect-ratio`.
❌ Do NOT show broken image icon (browser default) — always `onError` to the emoji placeholder.
❌ Do NOT require Google Places API key for images — must work in zero-key fallback mode.
