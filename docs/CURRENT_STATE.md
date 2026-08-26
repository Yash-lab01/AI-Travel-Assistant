# Current Project State
> Last updated: 2026-08-25

---

## Project Overview

**WanderAI** is a versatile multi-agent AI travel planner designed to plan complete, personalized day-by-day itineraries across any global or regional destination — seamlessly balancing iconic must-see sights, authentic hidden gems, budget constraints, and spatial pacing.

---

## What's Completed

### Phase 0 — Foundations (100% ✅)
- FastAPI backend with `/plan` (REST), `/plan/stream` (SSE), `/health`, `/export/pdf`
- LangGraph `StateGraph` with SQLite checkpointer (`data/checkpoints.db`) and JsonPlusSerializer
- All Pydantic schemas: `TripRequest → Stop → DayPlan → Itinerary → AgentEvent`
- Embedded Chroma vector store at `backend/data/chroma_db/` (`niche_spots` + `itineraries`)
- Log-normalised hidden gem scoring formula (7/7 unit tests passing)
- Next.js 16 frontend with "Nocturnal Voyager" dark design system
- Multi-section scrollable landing page & HTML5 Canvas Live Wallpaper
- Leaflet + CartoDB Dark Matter map integration (zero token / free)

### Phase 1 — Real Data Pipeline & Spatial Clustering (100% ✅)
- Intake Agent (Gemini 3.5 Flash / Groq slot extraction + robust regex fallback)
- Places Tool (Nominatim geocoding + OpenTripMap flat JSON parser + Google Places enrichment)
- Planner Agent (K-means++ coordinate clustering + Gemini 3.5 Flash destination-aware themes & narrations)

### Phase 2 — Niche Signal Scraping & Scoring Engine (100% ✅)
- Tavily travel search tool (`tavily_tool.py`) with blog & Reddit snippet extraction
- Reddit public discussion scraper (`reddit_tool.py`) with zero auth / zero key requirement
- Niche scraper & scoring pipeline (`niche_scraper.py`) with VADER sentiment intensity analysis
- Ranker Agent (`ranker_agent.py`) blending mainstream attractions and authentic hidden gems by `niche_weight`
- Guaranteed non-empty `ranked_stops` output — planner never bypasses the ranker
- 11/11 tests passing in pytest suite

### Phase 3 — Real-World Enhancements & UX Polish (100% ✅)
1. **Conversational Clarifications**: Detects brief prompts and asks 2–3 targeted questions with interactive chips, preserving destination across turns.
2. **Regional Multi-Zone Dispersion**: Queries distinct subzone centroids for states/regions (Goa, Rajasthan, Bali, Mumbai, Pune, Delhi, Kerala, Jaipur, Tokyo, Lisbon) for broad geographic day-by-day distribution.
3. **Transit Times & Weather**: Routing tool calculates sequential travel times; Open-Meteo provides live daily weather forecasts per day.
4. **Smart Currency Formatter**: Displays `₹ INR` for all Indian destinations and `$ USD` for international trips.
5. **Nocturnal Planning Studio UI**: Centered conversational studio unfolding into an interactive side-by-side Timeline + Map visualizer.
6. **Error-Proof Resiliency**: Safe LLM string extraction (`safe_extract_text`), guaranteed `k` day clustering, and safe Leaflet marker bounds.

### Phase 3 — Hardening Pass (100% ✅)
7. **K-means++**: Replaced index-seeded initialization — Day 1 no longer underpopulated. Post-clustering rebalance pass caps stop-count variance.
8. **Versioned Chroma Cache (`v6`)**: Old stale/mock data auto-bypassed. Cache writes only store `source="opentripmap"` stops. Increment `CACHE_VERSION` in `places_tool.py` on schema changes.
9. **Ranker Non-Empty Guarantee**: `ranker_node` always outputs `ranked_stops` (falls back to popular-only if niche scraper fails). `planner_node` logs `[WARNING]` on any bypass.
10. **Gemini Theme Fix**: Code-fence stripping before JSON parse; destination-aware fallback themes for Mumbai, Pune, Goa, Delhi, Jaipur, Kerala, Bali, Lisbon, Tokyo.

### Phase 4 — Image Integration, Visual Richness & UX Fixes (100% ✅)

#### 4a — Backend Image Sourcing
11. **Curated Destination Banners (`destination_images.py`)**: 25+ high-res landscape cover images for Indian and global destinations.
12. **4-Tier Wikipedia OpenSearch + PageImages Image Cascade** (`places_tool.py`):
    - Tier 1: Wikipedia REST Summary API (instant exact article lead photo)
    - Tier 2: Wikipedia OpenSearch API (canonical article discovery -> lead photo)
    - Tier 3: Wikipedia Generator Search with PageImages (fuzzy keyword matching)
    - Tier 4: Wikimedia Commons direct search (CC-licensed photography)
    - 100% verified real landmark photo hit rate across test benchmark. Zero auth required.
13. **All stops enriched**: `enrich_with_google_places()` enriches all unique POIs (not capped). Priority: Google Places → Wikipedia OpenSearch cascade → category curated fallback.
14. **Niche spot photos**: `niche_scraper.py` concurrently fetches real Wikipedia photos for community spots.
15. **Cache v7**: Auto-refreshes all cached POIs with high-resolution real photography.

#### 4b — Frontend Visual Components
16. **Visual Day Banners & Itinerary Cover**: Full-bleed hero imagery for itinerary headers and day tabs with gradient overlays.
17. **StopCard Photographic Thumbnails**: Shimmer skeleton loading state, lazy loading, and robust `onError` fallback to category icons.
18. **Landing Page 100vh Intro Screen & Destination Cards**: Minimalist brand hero with animated scroll indicator and photographic prompt cards.
19. **Map Marker Popup Thumbnails**: High-resolution image thumbnails embedded in Leaflet marker popups.

#### 4d — UX Bug Fixes
20. **Leaflet `fitBounds` fix**: `invalidateSize()` + 50ms defer + identical-coord `setView` fallback — eliminates console error on page load.
21. **Page scroll-jump fix**: `AgentEventFeed.tsx` and `ChatPanel.tsx` now use internal container `scrollTop` instead of global `scrollIntoView`. `page.tsx` adds `scrollRestoration='manual'` and `scrollTo(0,0)` on mount.

#### 4e — Multi-Turn Conversational Editing & State Iteration (100% ✅)
22. **Multi-Turn Intent Classifier (`intake_agent.py`)**: Classifies follow-ups (`new_trip`, `swap_stop`, `remove_stop`, `adjust_pace`, `change_budget`, `tell_me_more`, `general_edit`) and extracts target stop and day parameters.
23. **LangGraph Editor Agent (`editor_agent.py`)**: State patching node that swaps POIs (with candidate deduplication & 3-tier Wikipedia photo resolution), removes stops, recalculates sequential transit times, updates costs, and generates insider guides.
24. **Interactive StopCard Quick Actions (`ItineraryView.tsx`)**: `🔄 Swap`, `❌ Remove`, and `💬 Tell Me More` buttons on each attraction card.
25. **One-Click Quick Adjustment Chips**: Relaxed pacing, hidden gems, foodie focus, and scenic views adjustments.
26. **Targeted Endpoints & SSE Messages**: `PATCH /plan/{itinerary_id}/stop` endpoint and SSE `assistant_message` streaming.

#### 4f — Trip History & Saved Itinerary Browser (100% ✅)
27. **Backend SQLite Trip History Store (`history_store.py`)**: Auto-creates `backend/data/trip_history.db` with CRUD operations and auto-pruning to 50 trips.
28. **Trip History REST Endpoints (`main.py`)**: `GET /history`, `POST /history`, `GET /history/{id}`, `DELETE /history/{id}`.
29. **Dual-Layer Auto-Saving**: Every generated or edited itinerary is instantly saved to `localStorage` (up to 10 trips) and synced to the backend SQLite store.
30. **Trip History Slide-Over Panel (`TripHistoryPanel.tsx`)**: Visual cards with landscape cover thumbnails, duration & cost tags, relative timestamps, instant load button, and delete action.
31. **Nav Header History Badge (`page.tsx`)**: Dynamic badge indicator showing saved trip count and 1-click drawer toggle.
32. **19/19 Unit Tests Passing**: Full CRUD and pruning test suite in `test_history_store.py`.

---

## What's Next

### Phase 5 — Local Fine-Tuned Narration Model (LoRA) (NEXT 🔜)
- LoRA fine-tuning on Llama 3.2 3B with Unsloth + PEFT (Colab T4)
- Local Ollama deployment for zero-latency atmospheric narration
- Blind before/after evaluation in `eval_results.md`

### Phase 6 — Export, Sharing & Production Polish
- Playwright PDF export, shareable URL slugs, Leaflet polyline route overlay

---

## Reference Documents
- [`docs/IMAGE_INTEGRATION.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/docs/IMAGE_INTEGRATION.md) — Full image implementation spec (3-tier Wikipedia cascade, frontend changes, schema updates, what NOT to do).
- [`docs/TROUBLESHOOTING_AND_MISTAKES.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/docs/TROUBLESHOOTING_AND_MISTAKES.md) — Persistent log of 12 known pitfalls, model quirks, and rules for what NOT to do.
- [`.context/PROJECT_CONTEXT.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/.context/PROJECT_CONTEXT.md) — Architecture, active model names, Chroma path, coding conventions.
- [`.context/TASKS.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/.context/TASKS.md) — Granular phase task checklist.
- [`.context/HANDOFF.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/.context/HANDOFF.md) — Latest session bug fixes & immediate next steps.
