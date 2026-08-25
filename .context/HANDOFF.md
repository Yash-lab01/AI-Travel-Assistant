# HANDOFF.md — Active Session Handoff
> Last updated: 2026-08-25

## 1. Bugs Diagnosed & Resolved (All Sessions)

1. **`AttributeError: 'list' object has no attribute 'strip'` in LLM Invocations**:
   - **Root Cause**: In recent `langchain_google_genai` releases, `response.content` returns a list of dictionaries instead of a plain string.
   - **Fix**: `safe_extract_text(content: Any)` added to `intake_agent.py`, `planner_agent.py`, and `niche_scraper.py`.

2. **OpenTripMap Flat JSON vs GeoJSON Parser Miss & Mock Fallback**:
   - **Root Cause**: `fetch_otm_places` looked for `properties.xid` (GeoJSON). OTM returns flat JSON, so all real places were skipped.
   - **Fix**: Parser updated to read both flat JSON and GeoJSON shapes. Regional centroids added for Pune, Mumbai, Delhi, Jaipur, Goa, Kerala, Bali, Tokyo, Lisbon.

3. **Frontend Day Switching & Map Crash on Tab Click**:
   - **Root Cause**: `planner_agent.py` didn't strictly guarantee k clusters; `days[activeDay]` became `undefined`. Leaflet `fitBounds` on empty arrays threw errors.
   - **Fix**: Strict k-cluster guarantee in `_kmeans_cluster`; safe `validActiveDay` indexing in `ItineraryView.tsx`; lat/lon validation in `MapView.tsx`.

4. **Chroma Cache Serving Stale Mock Stops Across Cities**:
   - **Fix**: `CACHE_VERSION` system added to `places_tool.py`. Currently at **v6**. Increment when schema or parser changes.

5. **K-means Day 1 Consistently Underpopulated (1-2 Stops)**:
   - **Fix**: Replaced with **K-means++** initialization + post-clustering rebalance pass.

6. **Ranker Agent Bypassed — Planner Fetched Its Own OTM Data**:
   - **Fix**: `ranker_node` now guarantees never-empty `ranked_stops`. `planner_node` logs `[WARNING]` if ever triggered as last resort.

7. **Day Themes Always Show Generic Fallback Strings**:
   - **Fix**: Added code-fence stripping before JSON parse. Added destination-aware fallback themes for all major cities.

8. **Wikipedia Exact Title Miss — Generic Category Images on All Places**:
   - **Root Cause**: Old `fetch_wikimedia_image` used only exact `titles=` query; failed for most OTM place names.
   - **Fix**: Implemented **3-tier image cascade** in `places_tool.py`:
     1. Wikipedia REST Summary API (`/api/rest_v1/page/summary/{name}`)
     2. Wikipedia Generator Search (`action=query&generator=search&gsrsearch={name}`)
     3. Wikimedia Commons file search (`gsrnamespace=6`)
   - Result: ~100% real landmark image match rate tested on 23 Indian places.
   - Same cascade now used in `niche_scraper.py` for community spots.
   - **Cache bumped to v6** to auto-refresh all cached POIs.

9. **Leaflet `fitBounds` Error: "Bounds are not valid"**:
   - **Root Cause**: `map.fitBounds()` called before DOM layout calculated (0×0 container) or all stops at identical coords.
   - **Fix** in `MapView.tsx`: `invalidateSize()` + 50ms `setTimeout` defer + identical-coord `setView` fallback.

10. **Page Auto-Scrolling to Chat Section on Initial Load**:
    - **Root Cause**: `AgentEventFeed.tsx` called `element.scrollIntoView()` on mount with empty events array, which jumps the global viewport.
    - **Fix**: Replaced with internal container `scrollTop`/`scrollTo` in both `AgentEventFeed.tsx` and `ChatPanel.tsx`. Added `window.history.scrollRestoration = 'manual'` + `window.scrollTo(0,0)` in `page.tsx`.

---

## 2. Documentation Updated

- ✅ `.context/PROJECT_CONTEXT.md` — Corrected model names, Chroma path, coding conventions.
- ✅ `.context/TASKS.md` — Updated to reflect all Phase 4 sub-tasks + Phase 4e naming standardized, cache v6.
- ✅ `.context/HANDOFF.md` — This file (fully current as of 2026-08-25).
- ✅ `docs/CURRENT_STATE.md` — Updated Phase 4 items and correct cache version.
- ✅ `docs/TROUBLESHOOTING_AND_MISTAKES.md` — Entries #1–#12 covering all bugs encountered.
- ✅ `docs/IMAGE_INTEGRATION.md` — Updated Tier 1 from old single-query to actual 3-tier cascade.

---

## 3. Current Working State

- **Backend**: FastAPI server `http://127.0.0.1:8000` — running with `--reload`.
- **Frontend**: Next.js 16 `http://localhost:3000` — compiled with 0 errors.
- **Pytest**: 11/11 tests passing.
- **Chroma Cache**: Versioned at **v6** — all stale/mock data auto-bypassed.
- **Image Resolution**: 3-tier Wikipedia REST → Search → Commons, ~100% real landmark coverage.
- **Git**: All changes committed with separate `backend:`, `frontend:`, `docs:` commits and pushed to GitHub (`main`).

---

## 4. Immediate Next Steps — Phase 4e: Multi-Turn Conversational Editing

> Phase naming: All "Phase 4b" references in older docs now standardized to **Phase 4e**.

1. **Intent Classifier Node**: Add `classify_intent` node to LangGraph: `new_trip` | `edit_stop` | `adjust_pace` | `change_budget`.
2. **LangGraph Checkpoint Recovery**: Use existing SQLite checkpointer to retrieve and patch prior `TravelGraphState` without full replan.
3. **UI Edit Actions**: Add "Swap / Remove / Tell me more" quick-action buttons on `StopCard` in `ItineraryView.tsx` that pre-fill the chat input for the intent classifier.
4. **`PATCH /plan/{id}/stop` Endpoint**: Targeted backend endpoint for single-stop replacement without full replanning.
