# HANDOFF.md — Active Session Handoff

## 1. Bugs Diagnosed & Resolved in this Session

1. **`AttributeError: 'list' object has no attribute 'strip'` in LLM Invocations**:
   - **Root Cause**: In recent `langchain_google_genai` releases, `response.content` returns a list of dictionaries (`[{'type': 'text', 'text': '...'}]`) instead of a plain string. Calling `.strip()` directly broke theme generation, narrations, and extraction.
   - **Fix**: Created `safe_extract_text(content: Any)` across `intake_agent.py`, `planner_agent.py`, and `niche_scraper.py` to extract pure string text regardless of response shape.

2. **OpenTripMap Flat JSON vs GeoJSON Parser Miss & Mock Fallback**:
   - **Root Cause**: In `places_tool.py`, `fetch_otm_places` looked for `properties.xid` (GeoJSON shape). Because OpenTripMap returns flat JSON objects (`{"xid": "...", "name": "...", "point": {"lat": ..., "lon": ...}}`), all real attractions were skipped, returning 0 places and falling back to 8 hardcoded mock items like *"Scenic Waterfront Promenade"*.
   - **Fix**: Updated parser to read both flat JSON and GeoJSON shapes, filtering for valid place names. Subzone misses now return empty arrays without mixing mock data into real attraction lists. Added regional centroids for Pune, Mumbai, Delhi, Jaipur, Lisbon, and Goa.

3. **Frontend Day Switching & Map Error on Click**:
   - **Root Cause**: `planner_agent.py` did not strictly guarantee `k` day clusters when stop lists were rebalanced, leaving `days[activeDay]` `undefined` when clicking day tabs, crashing `ItineraryView.tsx`. Also `MapView.tsx` threw Leaflet bounds errors on invalid lat/lon values.
   - **Fix**:
     - `planner_agent.py` strictly guarantees returning exactly `trip.num_days` non-empty clusters.
     - `ItineraryView.tsx` implements safe active day indexing (`validActiveDay`).
     - `MapView.tsx` validates lat/lon coordinates and guards `bounds.isValid()`.

4. **Created Dedicated Troubleshooting Guide**:
   - Created [`docs/TROUBLESHOOTING_AND_MISTAKES.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/docs/TROUBLESHOOTING_AND_MISTAKES.md) covering all past errors, root causes, and explicit "What NOT to do" guidelines.

---

## 2. Current Working State
- **Backend**: FastAPI server running on `http://127.0.0.1:8000`.
- **Frontend**: Next.js 16 running on `http://localhost:3000`.
- **Pytest**: 11/11 tests passing.
- **Next.js Build**: 0 errors.

---

## 3. Immediate Next Steps (Phase 4)
1. **Multi-Turn Intent Classifier**: Add intent classification node (`new_trip`, `edit_stop`, `adjust_pace`, `change_budget`) to allow interactive chat modifications.
2. **Interactive State Patching**: Enable modifying individual stops, swapping venues, or regenerating specific days from conversational feedback.
