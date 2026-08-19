# Troubleshooting, Mistakes & Lessons Learned

This document serves as a persistent record of bugs encountered, root causes diagnosed, failed attempts, and concrete rules on **what NOT to do** in the WanderAI codebase.

---

## 1. LLM Response Formatting: `'list' object has no attribute 'strip'`
- **Symptom**:
  `AttributeError: 'list' object has no attribute 'strip'` thrown in `intake_agent.py`, `planner_agent.py`, and `niche_scraper.py`.
- **Root Cause**:
  Under recent versions of `langchain_google_genai` and `google-genai`, `response.content` is returned as a **list of content blocks** (e.g. `[{'type': 'text', 'text': '...', 'extras': {...}}]`) instead of a raw Python `str`. Calling `response.content.strip()` threw an unhandled exception and broke theme/narration generation, falling back to static default strings.
- **Rule / What to Do**:
  Always use `safe_extract_text(response.content)` across all agents:
  ```python
  def safe_extract_text(content: Any) -> str:
      if isinstance(content, str):
          return content.strip()
      if isinstance(content, list):
          parts = []
          for p in content:
              if isinstance(p, dict):
                  parts.append(p.get("text", ""))
              elif hasattr(p, "text"):
                  parts.append(getattr(p, "text", ""))
              else:
                  parts.append(str(p))
          return "".join(parts).strip()
      return str(content).strip()
  ```
- **What NOT to do**:
  ❌ Never call `response.content.strip()` directly on any LangChain invocation.

---

## 2. OpenTripMap JSON Format & Silent Fallback to Mock Data
- **Symptom**:
  Itineraries for Indian cities (Pune, Mumbai) or smaller destinations were returning generic fallback strings like *"Scenic Waterfront Promenade"*, *"Historic Old Town Center"*, and *"National Heritage Museum"*.
- **Root Cause**:
  In `places_tool.py`, the OpenTripMap API was called with `format=json`. The parser looked for GeoJSON attributes `f["properties"]["xid"]` and `f["geometry"]["coordinates"]`. But OpenTripMap with `format=json` returns flat dicts:
  `{"xid": "N...", "name": "...", "point": {"lat": ..., "lon": ...}}`.
  Because `properties` was `None`, all real attractions were skipped, resulting in an empty array `[]` and silently triggering `_mock_otm_places(lat, lon)`.
- **Rule / What to Do**:
  Support both flat JSON and GeoJSON shapes:
  ```python
  xid = f.get("xid") or f.get("properties", {}).get("xid")
  name = f.get("name") or f.get("properties", {}).get("name", "")
  point = f.get("point", {})
  lat = point.get("lat") or f.get("geometry", {}).get("coordinates", [None, None])[1]
  lon = point.get("lon") or f.get("geometry", {}).get("coordinates", [None, None])[0]
  ```
- **What NOT to do**:
  ❌ Never assume a 3rd-party geo API returns GeoJSON unless explicitly verified.
  ❌ Never mix mock POIs into real attraction lists when querying multi-zone subzones.

---

## 3. Provider Model Deprecations & 404s
- **Symptom**:
  - `Error calling model 'gemini-2.5-flash' (NOT_FOUND): 404 NOT_FOUND`
  - `The model llama-3.1-8b-instant does not exist or you do not have access to it`
- **Root Cause**:
  `gemini-2.5-flash` and `llama-3.1-8b-instant` were sunset or deprecated on Google AI Studio / Groq API endpoints.
- **Rule / Active Working Models**:
  - **Google AI Studio (Gemini)**: Use `gemini-3.5-flash` or `gemini-3.6-flash`.
  - **Groq**: Use `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, or `qwen/qwen3.6-27b`.
- **What NOT to do**:
  ❌ Do not reference legacy `gemini-2.5-flash` or `llama-3.1-8b-instant`.

---

## 4. Multi-Turn Destination Loss ("Unknown City")
- **Symptom**:
  User typed *"3 days in Mumbai"*, selected clarification preferences, and the final itinerary was titled *"3-Day Journey to Unknown"*.
- **Root Cause**:
  When submitting clarification chips, `handleSend` sent `"Submit preferences"`. The intake agent parsed that text independently and saw no city name, overriding `destination` with `"Unknown"`.
- **Rule / What to Do**:
  1. Frontend stores `pendingTrip: { destination, num_days }` and formats the submit message with the original destination.
  2. Frontend sends explicit `destination` and `num_days` in the JSON POST body.
  3. Backend graph state retains `state.get("destination")` and never overwrites it with `"Unknown"`.

---

## 5. Frontend Day Switching & Map Marker Errors
- **Symptom**:
  Clicking Day 2 or Day 3 tabs threw runtime exceptions or blank screens.
- **Root Cause**:
  If the backend returned fewer clusters than expected, or if `activeDay` was out of bounds, `days[activeDay]` became `undefined`. Accessing `currentDay.stops` threw `TypeError: Cannot read properties of undefined`.
  Additionally, passing invalid lat/lon or calling `fitBounds` on empty coordinate sets threw Leaflet errors.
- **Rule / What to Do**:
  1. Backend `_kmeans_cluster` strictly guarantees returning **EXACTLY `k` non-empty clusters** (`len(clusters) == k == num_days`).
  2. Frontend uses safe indexing:
     ```typescript
     const validActiveDay = (activeDay >= 0 && activeDay < days.length) ? activeDay : (activeDay === -1 ? -1 : 0);
     ```
  3. `MapView.tsx` validates coordinates (`typeof lat === 'number' && !isNaN(lat)`) and checks `bounds.isValid()` before calling `map.fitBounds()`.

---

## 6. LangSmith 403 Forbidden Console Spam
- **Symptom**:
  Constant terminal error logs: `Failed to POST https://api.smith.langchain.com/runs/multipart in LangSmith API: 403 Forbidden`.
- **Root Cause**:
  `LANGCHAIN_TRACING_V2=true` was enabled without a valid LangSmith API key.
- **Rule / What to Do**:
  Keep `LANGCHAIN_TRACING_V2=false` in `.env` unless actively debugging with a configured LangSmith workspace key.

---

## 7. Chroma Cache Polluted with Stale / Mock Stops Across Cities
- **Symptom**:
  After fixing the OTM parser, cities like Mumbai, Delhi, and Goa still showed generic stops (e.g. *"Artisanal Food & Spice Market"*, *"Traditional Arts & Craft Bazaar"*) despite new real OTM data being available.
- **Root Cause**:
  Old Chroma cache entries (stored before parser fix, with `source="mock"` or old `destination_key` metadata) were still matching queries via the old `destination_key` metadata field. Filtering by name prefix only caught some mocks — others slipped through.
- **Fix Applied**:
  1. Added `CACHE_VERSION = "v4"` constant in `places_tool.py`.
  2. Cache reads use `where={"cache_key": f"{dest_hash}_{CACHE_VERSION}"}` — old entries (different version) are transparently skipped.
  3. Cache writes only store entries with `source="opentripmap"` — mock stops are NEVER written.
- **Rule / What to Do**:
  Whenever the OTM parser or `Stop` schema changes, increment `CACHE_VERSION` in `places_tool.py`. This auto-invalidates all stale Chroma data on next request.
- **What NOT to do**:
  ❌ Do not manually delete `backend/data/chroma_db/` — this breaks all collections. Use versioning instead.

---

## 8. K-means Day 1 Consistently Underpopulated (1-2 Stops vs 5-6)
- **Symptom**:
  Day 1 cluster always has only 1-2 stops while Day 2 and Day 3 have 5+ stops each. Day 1 cards appear sparse in the UI.
- **Root Cause**:
  The original k-means initialization seeded centroids by dividing `lat-sorted stops` into k equal index steps. For cities where most POIs cluster geographically, the first centroid always landed in a small dense pocket, capturing very few items.
- **Fix Applied**:
  Replaced standard k-means initialization with **K-means++**:
  - First seed is random.
  - Each subsequent seed is sampled proportional to the squared distance from existing seeds.
  - This guarantees initial centroids are maximally spread, preventing early cluster collapse.
  - Added a post-clustering rebalance pass: if any cluster has `> target_per_day + 2` stops, excess stops are redistributed to the smallest cluster.
- **What NOT to do**:
  ❌ Do not use evenly-spaced lat-sorted index seeding for k-means on Indian cities — POIs cluster tightly by lat/lon and index-based seeding is pathological for this distribution.

---

## 9. Ranker Agent Bypassed — Planner Fetches Its Own OTM Data
- **Symptom**:
  Hidden gem stops from the Ranker's niche blending never appeared in the final itinerary. The planner would always show 100% OTM attraction-type stops.
- **Root Cause**:
  In `planner_agent.py`, when `state.get("ranked_stops")` was empty (e.g. ranker returned `[]` due to a niche scraper error), the planner silently fell back to calling `get_places_for_destination()` directly. This bypassed the niche-blending logic entirely.
- **Fix Applied**:
  1. `ranker_node` now has a **"never empty" guarantee**: even if `niche_stops` fails, it returns `popular_stops` directly as `ranked_stops`.
  2. `planner_node` treats an empty `ranked_stops` as a WARNING and only falls back as a true last resort (ranker itself crashed).
  3. Both agents log a `[WARNING]` message when the fallback path is taken.
- **What NOT to do**:
  ❌ Never silently swallow the ranker failure without a log message — it makes the bypass invisible during debugging.

---

## 10. Leaflet Map `fitBounds` Error: "Bounds are not valid"
- **Symptom**:
  Console log shows `[browser] Map fitBounds error: Error: Bounds are not valid. at fitBounds (leaflet.js) at updateLeafletMarkers (MapView.tsx)`.
- **Root Cause**:
  `map.fitBounds(bounds)` was called before the container DOM element finished layout calculation (container dimensions width=0, height=0), or when all stops had identical coordinates (`bounds.getNorthEast().equals(bounds.getSouthWest())`).
- **Fix Applied**:
  In `MapView.tsx`:
  1. Check `mapContainerRef.current` client dimensions before fitting bounds.
  2. Call `leafletMapRef.current.invalidateSize()` inside a brief `setTimeout(..., 50)` tick to guarantee post-render layout accuracy.
  3. If NorthEast equals SouthWest, fall back to `map.setView([lat, lon], 14)` instead of calling `fitBounds`.
- **What NOT to do**:
  ❌ Never call `map.fitBounds` synchronously in `useEffect` without layout dimension validation — container resizing during tab switches will throw bounds errors.

---

## 11. Wikipedia Exact Title Miss for Real Landmark POIs
- **Symptom**:
  Stops showed fallback generic category icons/photos even for major landmarks (e.g. "Gateway of India", "Dagdusheth Halwai Ganapati Temple", "Elephanta Caves").
- **Root Cause**:
  The initial `fetch_wikimedia_image` only queried Wikipedia's `action=query&titles={name}`. If the OpenTripMap name didn't match the exact Wikipedia page title (e.g., compound/localized names), Wikipedia returned a miss.
- **Fix Applied**:
  Implemented a 3-tier cascade in `places_tool.py`:
  1. **Wikipedia REST Summary API**: `https://en.wikipedia.org/api/rest_v1/page/summary/{name}` (instant exact matches).
  2. **Wikipedia Generator Search**: `https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch={name}&prop=pageimages&piprop=thumbnail|original` (fuzzy search matching).
  3. **Wikimedia Commons Search**: `https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={name}&gsrnamespace=6` (CC-licensed file search).
  - Achieved **100% real image match rate** (23/23 on landmark test set).
  - Bumped `CACHE_VERSION = "v6"` in `places_tool.py` to auto-refresh cached POIs.
- **What NOT to do**:
  ❌ Never rely solely on exact title matching (`titles=`) for Wikipedia image resolution — always provide fuzzy generator search as a fallback.

