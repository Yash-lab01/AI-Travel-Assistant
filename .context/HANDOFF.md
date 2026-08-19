# HANDOFF.md — Active Session Handoff
> Last updated: 2026-08-19

## 1. Bugs Diagnosed & Resolved in this Session

1. **`AttributeError: 'list' object has no attribute 'strip'` in LLM Invocations**:
   - **Root Cause**: In recent `langchain_google_genai` releases, `response.content` returns a list of dictionaries (`[{'type': 'text', 'text': '...'}]`) instead of a plain string.
   - **Fix**: `safe_extract_text(content: Any)` added to `intake_agent.py`, `planner_agent.py`, and `niche_scraper.py`.

2. **OpenTripMap Flat JSON vs GeoJSON Parser Miss & Mock Fallback**:
   - **Root Cause**: `fetch_otm_places` looked for `properties.xid` (GeoJSON). OTM returns flat JSON (`{"xid": "...", "name": "...", "point": {...}}`), so all real places were skipped and mock data was returned.
   - **Fix**: Parser updated to read both flat JSON and GeoJSON shapes. Regional centroids added for Pune, Mumbai, Delhi, Jaipur, Goa, Kerala, Bali, Tokyo, Lisbon.

3. **Frontend Day Switching & Map Crash on Tab Click**:
   - **Root Cause**: `planner_agent.py` didn't strictly guarantee k clusters; `days[activeDay]` became `undefined`. Leaflet `fitBounds` on empty arrays threw errors.
   - **Fix**: Strict k-cluster guarantee in `_kmeans_cluster`; safe `validActiveDay` indexing in `ItineraryView.tsx`; lat/lon validation in `MapView.tsx`.

4. **Chroma Cache Serving Stale Mock Stops Across Cities**:
   - **Root Cause**: Old cache entries (stored before parser fix, source=mock) still matched via old `destination_key` metadata. Name-prefix filtering only caught some.
   - **Fix**: `CACHE_VERSION = "v4"` added to `places_tool.py`. Cache reads query by `cache_key = f"{dest_hash}_v4"`, so old entries are transparently skipped. Only `source="opentripmap"` stops are written to cache.

5. **K-means Day 1 Consistently Underpopulated (1-2 Stops)**:
   - **Root Cause**: Centroid seeding was by evenly-spaced lat-sorted index — pathological for Indian cities where POIs cluster tightly, causing the first centroid to land in a tiny pocket.
   - **Fix**: Replaced with **K-means++** initialization (proportional-distance sampling) + post-clustering rebalance pass to cap stop-count variance across days.

6. **Ranker Agent Bypassed — Planner Fetched Its Own OTM Data**:
   - **Root Cause**: When `ranked_stops` was empty (e.g. niche scraper error), `planner_node` silently called `get_places_for_destination()` directly, bypassing niche blending.
   - **Fix**: `ranker_node` now guarantees **never-empty `ranked_stops`** (falls back to `popular_stops` if niche fails). `planner_node` logs `[WARNING]` if ever triggered as last resort.

7. **Day Themes Always Show Generic Fallback Strings**:
   - **Root Cause**: Gemini response sometimes included markdown code fences (` ```json `) which broke `re.search(r'\[.*\]')` match, silently falling through to hardcoded generic themes.
   - **Fix**: Added `re.sub(r'```(?:json)?', '', raw).strip()` to strip code fences before JSON parsing. Added destination-aware fallback themes for Mumbai, Pune, Goa, Delhi, Jaipur, Kerala, Bali, Lisbon.

---

## 2. Documentation Updated This Session

- ✅ `.context/PROJECT_CONTEXT.md` — Corrected model names, Chroma path, added Phase 3 tools to directory layout, added coding conventions for `safe_extract_text` and cache versioning.
- ✅ `.context/TASKS.md` — Phase 3 sub-tasks updated to reflect k-means++ and cache versioning fixes.
- ✅ `docs/CURRENT_STATE.md` — Updated to reflect Phase 3 hardening pass completion.
- ✅ `docs/TROUBLESHOOTING_AND_MISTAKES.md` — Added entries #7, #8, #9 (Chroma cache pollution, k-means imbalance, ranker bypass).

---

## 3. Current Working State
- **Backend**: FastAPI server `http://127.0.0.1:8000` — running with `--reload`.
- **Frontend**: Next.js 16 `http://localhost:3000`.
- **Pytest**: 11/11 tests passing.
- **Chroma Cache**: Versioned at `v4` — all old stale/mock data is bypassed automatically on next query.

---

## 4. Immediate Next Steps (Phase 4a — Images)

Images were identified as the single highest-impact missing feature. The entire app currently shows emoji-only placeholders on stop cards and has zero destination photography on the landing page.

**Design spec**: [`docs/IMAGE_INTEGRATION.md`](../docs/IMAGE_INTEGRATION.md)

### Start here (backend, in order):
1. **Create `backend/app/tools/destination_images.py`** — curated static Unsplash photo URLs for 15+ destinations (no API key, instant, reliable). Used for landing page cards + itinerary/day banners.
2. **Add `fetch_wikimedia_image(place_name)`** to `places_tool.py` — free Wikipedia pageimages API for CC-licensed stop photos (no key, high quality).
3. **Add `_unsplash_fallback_url(name, category, destination)`** to `places_tool.py` — keyword URL fallback when Wikimedia + Google Places both miss.
4. **Remove `num_days * 5` cap** on `enrich_with_google_places()` — enrich all stops, not just the top N.
5. **Add `cover_image_url: Optional[str]`** to `Itinerary` and `DayPlan` in `schemas.py` + `index.ts`.
6. **Populate `cover_image_url`** in `planner_agent.py`.

### Then frontend:
7. **`ItineraryView.tsx`** — full-bleed 16:9 stop card images with shimmer skeleton + `onError` fallback.
8. **`ItineraryView.tsx`** — `DayBanner` component with cover photo + dark gradient overlay.
9. **`page.tsx`** — add destination photos to `HERO_PROMPT_CARDS`.
10. **`MapView.tsx`** — photo thumbnail in Leaflet marker popups.
11. **`globals.css`** — proper `aspect-ratio: 16/9`, `object-fit: cover`, shimmer `@keyframes`.

### Key rules (from IMAGE_INTEGRATION.md):
- ❌ Never call Unsplash Source at render time — it randomizes. Generate URL once in backend.
- ❌ Never use `object-fit: contain` for destination photos.
- ❌ Never skip `loading="lazy"` — 15+ images will freeze the browser.
- ❌ Never show broken browser image icon — always `onError` to emoji placeholder.
- ✅ Must work in zero-key mode — all 3 tiers (Google → Wikimedia → Unsplash) must degrade gracefully.
