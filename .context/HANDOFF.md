# HANDOFF.md — Active Session Handoff
> Last updated: 2026-09-16

## 1. Bugs Diagnosed & Resolved (All Sessions)

1. **`AttributeError: 'list' object has no attribute 'strip'` in LLM Invocations**: `safe_extract_text()` added to `intake_agent.py`, `planner_agent.py`, `niche_scraper.py`.
2. **OpenTripMap Flat JSON vs GeoJSON Parser Miss**: Parser updated; regional centroids added for all major cities.
3. **Frontend Day Switching & Map Crash on Tab Click**: Strict k-cluster guarantee; safe `validActiveDay` indexing; lat/lon validation.
4. **Chroma Cache Serving Stale Mock Stops**: `CACHE_VERSION` system at **v6** in `places_tool.py`.
5. **K-means Day 1 Underpopulated**: Replaced with K-means++ initialization + post-clustering rebalance.
6. **Ranker Agent Bypassed**: `ranker_node` now guarantees never-empty `ranked_stops`.
7. **Day Themes Always Show Generic Fallback**: Code-fence stripping + destination-aware fallback themes.
8. **Wikipedia Exact Title Miss — Generic Category Images**: 4-tier image cascade (Wikipedia REST → Generator Search → Wikimedia Commons → Unsplash/Pexels). Cache bumped to v6.
9. **Leaflet `fitBounds` Error on initial render**: `invalidateSize()` + 50ms `setTimeout` defer + identical-coord fallback.
10. **Page Auto-Scrolling to Chat on Load**: Internal container scroll in `AgentEventFeed.tsx`/`ChatPanel.tsx` + `scrollRestoration = 'manual'` in `page.tsx`.
11. **Quick-edit chips broke the trip (Phase 7)**: Chips routed through `externalPrompt` → new trip with no context. Fixed by adding `externalEditInstruction` prop to `ChatPanel` so `existing_itinerary_id` is always sent.
12. **Leaflet polyline crash `TypeError: Cannot read undefined 'x'` (Phase 7)**: Polylines drawn before `invalidateSize()`. Fixed by moving polyline construction inside the 50ms `setTimeout`.

---

## 2. Documentation Updated

- ✅ `.context/TASKS.md` — Phase 7 section added (7A bugs, 7B dynamic clarifications, 7C planned)
- ✅ `.context/HANDOFF.md` — This file (fully current as of 2026-09-02)
- ✅ `.context/PROJECT_CONTEXT.md` — Dynamic clarification architecture documented
- ✅ `docs/COMPREHENSIVE_AUDIT_AND_ROADMAP.md` — Overkill features removed; Phase 7 roadmap refined for portfolio
- ✅ `README.md` — Updated feature list to include Phase 7 changes

---

## 3. Current Working State

- **Backend**: FastAPI `http://127.0.0.1:8000` running with `--reload`.
- **Frontend**: Next.js 16 `http://localhost:3000`, 0 TypeScript errors.
- **Pytest**: 31/31 tests passing.
- **Dynamic Clarifications (Phase 7B)**: `_generate_dynamic_clarification_questions()` in `intake_agent.py` — Gemini 2.0 Flash → Groq Llama 3.1 8B → static fallback chain. Questions are now prompt-specific.
- **Quick-edit chips fix (Phase 7A)**: `externalEditInstruction` prop routes edits with correct `existing_itinerary_id`.
- **Polyline crash fix (Phase 7A)**: Polylines now drawn inside `setTimeout` after `invalidateSize()`.
- **PDF Export (Phase 6)**: `GET /export/pdf/{id}` & `POST /export/pdf`. Playwright Chromium — **must install via `python -m playwright install chromium`**.
- **Shareable Public Trips (Phase 6)**: `/trip/[slug]` + `ShareModal` + `GET /share/{slug}`.
- **Sequential Route Polylines (Phase 6)**: Dual-layer glowing polylines in `MapView.tsx`.
- **Local LoRA Travel Narrator (Phase 5)**: `ml/ollama_narrator.py` zero-latency client.
- **Trip History (Phase 4f)**: SQLite + `localStorage` + `TripHistoryPanel` drawer.
- **Multi-Turn Editing (Phase 4e)**: `editor_agent.py` + StopCard actions (Swap, Remove, Tell Me More) + quick-edit chips.

---

## 4. Recent Issues Diagnosed & Resolved (Session September 2026)

13. **Model Deprecations (404 NOT_FOUND)**:
    - `gemini-2.5-flash` and `gemini-2.0-flash` were deprecated by Google.
    - `llama-3.1-8b-instant`, `llama-3.3-70b-versatile`, and `qwen/qwen3.6-27b` were deprecated or unavailable on Groq.
    - Migrated all agents (`planner_agent.py`, `intake_agent.py`, `editor_agent.py`, `packing_list_generator.py`, `niche_scraper.py`) to **`gemini-3.6-flash`** (with `gemini-3.5-flash` fallback) and Groq **`openai/gpt-oss-20b`** (with `openai/gpt-oss-120b`).
14. **Missing Groq Fallback in Planner Agent & Generic Narrations**:
    - `planner_agent.py` previously had no Groq fallback, so any Gemini 404 or 429 quota exhaustion defaulted all stop narrations to `"Iconic attraction in <destination>."`.
    - Added Groq `openai/gpt-oss-20b` fallback for themes and narrations (< 1s generation) + context-aware, category-specific descriptive narrations for museums, viewpoints, restaurants, markets, and attractions.
15. **Leaflet Map Blank / Stale Closure / Centered on Pune**:
    - `MapView.tsx` had a mount race condition where `mapReadyRef.current` was `false` during initial render, and the 120ms timeout closure captured empty `stops = []`, causing the map to stay permanently stuck on default Pune coordinates with no markers.
    - Container re-renders also triggered `Error: Map container is already initialized`.
    - Preloaded `leaflet.css` in `layout.tsx` `<head>`, stored `stops` in `stopsRef.current` to eliminate stale closures, added `_leaflet_id` deletion before initialization, and auto-centered on the first valid stop coordinates immediately.
16. **Destination Images 403 Forbidden & Missing Cities**:
    - Legacy Google Places photo API URLs returned `403 Forbidden` in browser `<img>` tags, triggering `onError` and turning cards into blank placeholders.
    - Removed failing Google Places photo URLs; routed directly to Wikipedia/Wikimedia Commons + curated photography; incremented `CACHE_VERSION` to `v8`.
    - Expanded `DESTINATION_BANNERS` with high-resolution photography for Hyderabad, Chennai, Kolkata, Amritsar, Ahmedabad, Kochi, Shimla, Hampi, Mysore, Pondicherry, Ooty, Srinagar, Jodhpur, Jaisalmer, Seoul, Amsterdam, Prague, Vienna, Istanbul, Cairo, Sydney.
    - Added two-tier image fallback in `StopCard` (`ItineraryView.tsx`) to fall back to curated category photos on image load errors.
17. **Anti-AI-Look Polish (`ANTI_AI_LOOK_PLAN.md`)**:
    - Restored center-aligned hero headline, subtitle, and action buttons (`R1`).
    - Changed button border radius from boxy 8px to sleek 12px (`var(--radius-md)`) (`R2`).
    - Updated intro badge copy to `✦ DESCRIBE YOUR TRIP · AI BUILDS THE REST` (`A1`).
    - Updated header badge to `Live · 6 Agents` (`A2`).
    - Renamed mobile nav tab 4 from `Architecture` to `How It Works` (`A3`).
18. **Generation Timeout & Latency Waste (Phase 10)**:
    - Frontend watchdog aborted after 45s due to 40 unthrottled NearbySearch calls and 40 serial Wikipedia searches on cold destinations.
    - Increasing watchdog to 90s, probing/bypassing inactive Google Places calls, and bounding Wikipedia searches.
19. **Niche Scraper `NameError: scored_candidates` (Phase 10)**:
    - `niche_scraper.py` line 115 failed on uninitialized `scored_candidates` list, breaking community gem discovery.
20. **Geocoding False Positive for Kashmir (Phase 10)**:
    - Nominatim geocoded `"Kashmir"` to a tiny village in the Barmer desert of Rajasthan (`26.2644, 71.6027`), resulting in 0 OTM places and generic mock fallbacks.
    - Adding fast-path overrides for Kashmir Valley (`34.0837, 74.7973`) and regional subzones (Srinagar, Gulmarg, Pahalgam, Sonamarg).
21. **Single-Image Category Repetition & Cache Poisoning (Phase 10)**:
    - Single static fallback URL per category caused repeated images across cards.
    - Adding rich category photo pools (8–10 photos per category) with deterministic name hashing + destination-specific photo collections; bumping cache to `v9` and forbidding mock caching under `source="opentripmap"`.

---

## 5. Active Developmental Milestone

Phase 10 (Performance Overhaul & Multi-Tier Photo Engine) is actively being implemented. All previous phases (0 through 9) are 100% completed and verified with 36/36 passing unit tests.


