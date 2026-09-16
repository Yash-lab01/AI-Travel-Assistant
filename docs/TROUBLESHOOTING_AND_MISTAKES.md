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
  - `Error calling model 'gemini-2.0-flash' (NOT_FOUND): 404 NOT_FOUND`
  - `The model llama-3.1-8b-instant does not exist or you do not have access to it`
  - `The model qwen/qwen3.6-27b does not exist or you do not have access to it`
- **Root Cause**:
  `gemini-2.5-flash`, `gemini-2.0-flash`, `llama-3.1-8b-instant`, `llama-3.3-70b-versatile`, and `qwen/qwen3.6-27b` were sunset or deprecated on Google AI Studio / Groq API endpoints.
- **Rule / Active Working Models (2026)**:
  - **Google AI Studio (Gemini)**: Use `gemini-3.6-flash` (primary) with `gemini-3.5-flash` (fallback).
  - **Groq**: Use `openai/gpt-oss-20b` (primary) with `openai/gpt-oss-120b` (fallback).
- **What NOT to do**:
  ❌ Do not reference sunset models `gemini-2.5-flash`, `gemini-2.0-flash`, `llama-3.1-8b-instant`, or `qwen/qwen3.6-27b`.

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

---

## 12. Page Auto-Scrolling to Chat Section on Initial Load
- **Symptom**:
  Opening or refreshing `http://localhost:3000` jumped the browser viewport directly to the Interactive Studio / Chat section instead of staying at the top hero section.
- **Root Cause**:
  `AgentEventFeed.tsx` had an active `useEffect(() => { bottomRef.current?.scrollIntoView(); }, [events])` which triggered on initial mount with `events = []`. Calling `element.scrollIntoView()` on an element inside a sub-component forces the global browser window/viewport to scroll down to that element.
- **Fix Applied**:
  1. Replaced `scrollIntoView()` in `AgentEventFeed.tsx` and `ChatPanel.tsx` with **internal container scrolling** (`containerRef.current.scrollTop = containerRef.current.scrollHeight` / `containerRef.current.scrollTo(...)`), which strictly scrolls only the message list inside the chat panel and never moves the outer browser window.
  2. In `page.tsx`, added `window.history.scrollRestoration = 'manual'` and `window.scrollTo(0, 0)` on mount to ensure the site always starts at the top hero section on load and refresh.
- **What NOT to do**:
  ❌ Never use `element.scrollIntoView()` inside child components for internal message lists — it affects the top-level viewport. Use `container.scrollTop = container.scrollHeight` on the scrollable container ref instead.

---

## 13. Quick-Edit Chips Bypassing Existing Itinerary Context (Phase 7A)
- **Symptom**:
  Clicking quick-edit chips (e.g. "🧘 Relaxed Pacing", "🍲 Foodie & Cafes") triggered a brand new itinerary generation from scratch instead of modifying the currently active trip.
- **Root Cause**:
  `onQuickEdit` routed through `externalPrompt` in `page.tsx`, which invoked `handleSend(prompt)` with no action context. The backend treated this as a fresh trip request and generated an entirely unrelated itinerary.
- **Fix Applied**:
  Added `externalEditInstruction` prop to `ChatPanel`, dispatching `handleSend(instruction, { action: 'edit_whole' })`, which guarantees `existing_itinerary_id` is passed to the backend `editor_node`.
- **What NOT to do**:
  ❌ Never route contextual edits through generic `externalPrompt` without specifying the target `existing_itinerary_id`.

---

## 14. Leaflet Polyline Race Condition (`TypeError: Cannot read properties of undefined (reading 'x')`)
- **Symptom**:
  Switching days in `MapView.tsx` or loading an itinerary occasionally threw `TypeError: Cannot read properties of undefined (reading 'x')` in `leaflet.js`.
- **Root Cause**:
  Sequential route polylines were constructed synchronously before Leaflet's container projection settled (via `invalidateSize()`). When `latLngToLayerPoint` was called on unprojected coordinates, `point.x` was undefined.
- **Fix Applied**:
  Moved polyline creation inside the 50ms deferred `setTimeout` block alongside `invalidateSize()`.
- **What NOT to do**:
  ❌ Never add `L.polyline` or query map layer projections synchronously during render before `invalidateSize()` executes.

---

## 15. Missing Groq Fallback in Planner Agent & Generic Narrations on Quota Exhaustion (429/404)
- **Symptom**:
  Every stop narration showed `"Iconic attraction in <destination>."` and day themes defaulted to `"Exploring <destination>"`.
- **Root Cause**:
  Unlike `intake_agent.py`, `planner_agent.py` had no secondary LLM fallback chain. When Google Gemini hit 429 quota exhaustion or returned 404 on deprecated models, the planner silently fell back to generic static string templates.
- **Fix Applied**:
  1. Integrated Groq `openai/gpt-oss-20b` fallback directly into `planner_agent.py` for day themes and stop narrations.
  2. Enhanced the fallback narrator with category-specific descriptions (viewpoints, museums, restaurants, markets, historic sites) based on stop metadata.
- **What NOT to do**:
  ❌ Never leave LLM nodes without a cross-provider fallback (e.g., Gemini → Groq) or contextual fallback templates.

---

## 16. Leaflet Map Stale Closure & `_leaflet_id` Container Reuse Crashes
- **Symptom**:
  Map remained permanently blank or frozen on default Pune coordinates (`[18.5204, 73.8567]`) with zero markers, or logged `Error: Map container is already initialized`.
- **Root Cause**:
  1. During mount, `mapReadyRef.current` was false. The initial 120ms timeout closure captured `stops = []` from the initial render, meaning subsequent stop updates were never plotted if `mapReadyRef` became true after `stops` settled.
  2. React unmount/remount cycles left the `_leaflet_id` property on the DOM element, causing Leaflet to throw an already-initialized exception.
- **Fix Applied**:
  1. Preloaded `leaflet.css` in `layout.tsx` `<head>` for instant tile styling.
  2. Stored `stops` in `stopsRef.current` to always access the latest stops across timeout closures.
  3. Explicitly cleared `(container as any)._leaflet_id = null` before calling `L.map(container)`.
  4. Centered map immediately on `stops[0]` coordinates when initializing if stops are already available.
- **What NOT to do**:
  ❌ Never capture reactive state variables (`stops`) inside delayed `setTimeout` closures without a mutable ref (`stopsRef.current`).

---

## 17. Google Places Legacy Photo URLs 403 Forbidden & StopCard Fallback
- **Symptom**:
  Place photos on `StopCard` broke and fell back to empty grey placeholders across all stops; console logged `403 Forbidden` on Google Places photo URLs.
- **Root Cause**:
  Legacy Google Places photo API endpoints (`maps.googleapis.com/maps/api/place/photo`) returned `403 Forbidden` when embedded in browser `<img>` tags due to API key referrer restrictions / billing enforcement.
- **Fix Applied**:
  1. Removed legacy Google Places photo URLs from `places_tool.py` and routed directly to the Wikipedia REST Summary API, Wikipedia OpenSearch API, and Wikimedia Commons lead images.
  2. Incremented `CACHE_VERSION = "v8"` in `places_tool.py` to flush broken URLs from Chroma cache.
  3. Added a two-tier fallback in `StopCard` (`ItineraryView.tsx`): if a photo URL fails, fall back to curated high-resolution category photography (`getCategoryFallbackPhoto()`), and only show the emoji icon if category fallback fails.
  4. Expanded `DESTINATION_BANNERS` in `destination_images.py` with 20+ additional cities.
- **What NOT to do**:
  ❌ Never embed key-restricted Google Places photo URLs directly in client-side `<img>` tags without verifying referrer and billing policies.

---

## 18. Niche Scraper Variable Uninitialized (`NameError: name 'scored_candidates' is not defined`)
- **Symptom**:
  Terminal log showed `[ranker_agent] Niche discovery failed for '<destination>': name 'scored_candidates' is not defined`. No community hidden gems were blended; only mainstream or mock stops appeared.
- **Root Cause**:
  In `niche_scraper.py`, `scored_candidates` was appended to inside the candidate scoring loop without prior declaration `scored_candidates: list[dict] = []` at the top of the function.
- **Fix Applied**:
  Declared `scored_candidates: list[dict] = []` adjacent to `stops: list[Stop] = []` prior to scoring loop execution.
- **What NOT to do**:
  ❌ Never append to a local accumulator list inside a loop without explicit initial declaration.

---

## 19. Geocoding False Positives (e.g. Kashmir Resolving to Barmer Desert, Rajasthan)
- **Symptom**:
  Planning a trip for "Kashmir" resulted in 0 OpenTripMap attractions and fell back to 8 generic mock places in the middle of nowhere.
- **Root Cause**:
  Nominatim returned a tiny village in Barmer, Rajasthan (`26.2644, 71.6027`) as the top result for "Kashmir" instead of the Jammu & Kashmir region or Srinagar Valley.
- **Fix Applied**:
  1. Added explicit fast-path centroid overrides in `geocode_destination` for regional destinations (`kashmir` → `34.0837, 74.7973`, `ladakh` → `34.1526, 77.5771`, `himachal/manali` → `32.2396, 77.1887`).
  2. Added Kashmir to `REGIONAL_SUBZONES` with Srinagar, Gulmarg, Pahalgam, and Sonamarg centroids.
- **What NOT to do**:
  ❌ Never blindly trust top-1 free text geocoder results for wide geographical regions or territories without checking against known region overrides.

---

## 20. Google Places NearbySearch Latency Sink & 45s Frontend Watchdog Abort
- **Symptom**:
  Frontend aborted with `⚠️ Connection to planner timed out after 45 seconds.` On retry, generation succeeded in ~15s.
- **Root Cause**:
  1. `ChatPanel.tsx` had an aggressive 45s abort watchdog.
  2. `places_tool.py` executed `enrich_with_google_places` for 30–50 items concurrently. Since Google Places NearbySearch was unauthorized or returned `{}` for each item, this wasted ~15–20s of HTTP timeout time on cold destinations before Wikipedia even started.
- **Fix Applied**:
  1. Extended `ChatPanel.tsx` watchdog to 90 seconds for multi-day cold queries.
  2. Probed Google Places key once; if unauthorized or empty, short-circuit and skip the 40-request `nearbysearch` loop entirely.
- **What NOT to do**:
  ❌ Never execute dozens of external API calls in a loop without probing whether the provider/credential is actually responsive and authorized.

---

## 21. Single-Image Category Repetition & Mock Cache Poisoning
- **Symptom**:
  All stop cards in the same category (e.g. 5 attractions) displayed the exact same fallback photo. Additionally, mock stops were permanently cached in Chroma as real OTM data.
- **Root Cause**:
  1. `CATEGORY_FALLBACK_IMAGES` had only 1 static URL per category.
  2. `places_tool.py` labelled mock fallback stops as `source="opentripmap"`, permanently writing them into Chroma cache under `v8`.
- **Fix Applied**:
  1. Created multi-image pools (8–10 distinct high-resolution Unsplash photos per category) with deterministic name hashing (`hash(stop.name) % pool.length`).
  2. Added dedicated destination photo libraries (e.g. Kashmir, Goa, Mumbai, Jaipur, Kerala) so fallbacks use authentic regional photos.
  3. Ensured mock stops are labelled `source="mock"` and never written to Chroma.
  4. Bumped cache to `CACHE_VERSION = "v9"` to purge poisoned legacy entries.
- **What NOT to do**:
  ❌ Never use a single static image fallback for an entire category. Always use diverse photo pools or hash-based selection to avoid duplicate card imagery.




