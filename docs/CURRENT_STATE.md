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

### Phase 5 — Local Fine-Tuned Narration Model (LoRA) (100% ✅)
33. **Dataset Curation (`ml/curate_dataset.py`)**: 320 structured atmospheric travel writing pairs exported to `ml/dataset/train.jsonl` (288) and `ml/dataset/eval.jsonl` (32).
34. **LoRA Fine-Tuning Script (`ml/train_lora.py`)**: Unsloth + PEFT + TRL pipeline for Llama 3.2 3B Instruct (4-bit QLoRA, rank=16, alpha=32, target projections, GGUF export).
35. **Google Colab Runnable Notebook (`ml/train_colab_notebook.ipynb`)**: Ready-to-run GPU notebook with dataset loading, SFTTrainer loop, inference test, and GGUF packaging.
36. **Ollama Modelfile (`ml/Modelfile`)**: Pre-configured parameters (temperature=0.4, anti-cliché system prompt) for Ollama serving.
37. **Local Ollama Narrator Tool (`backend/app/tools/ollama_narrator.py`)**: Zero-latency local LLM client integrated into `planner_agent.py` and `editor_agent.py` with multi-tier fallback.
38. **Qualitative & Automated Benchmark Evaluation (`docs/eval_results.md`)**: Comprehensive 10-landmark evaluation demonstrating 88.0/100 quality score and 0% cliché frequency.
39. **24/24 Pytest Unit Tests Passing**: 100% passing across test suite including mock Ollama tests.

### Phase 6 — Export, Sharing & Production Polish (100% ✅)
### Phase 6 — Export, Sharing & Production Polish (100% ✅)
40. **Headless Playwright PDF Export Service (`pdf_generator.py`)**: High-fidelity A4 PDF travel brochure generator formatting Google Fonts, destination hero banner, day weather forecasts, numbered stop cards, durations, costs, real photography, and atmospheric narrations.
41. **Dual PDF Export Endpoints (`main.py`)**: `GET /export/pdf/{itinerary_id}` for saved trips and `POST /export/pdf` for immediate in-memory export.
42. **Public Shareable Trip Route (`frontend/src/app/trip/[slug]/page.tsx`)**: Standalone, public read-only page with day tabs, interactive map, stop details, and "✨ Plan Your Own Trip" CTA.
43. **Interactive Share Modal (`ShareModal.tsx`)**: 1-click Copy Share Link, WhatsApp, X (Twitter), and Email direct sharing buttons.
44. **Sequential Leaflet Route Overlays (`MapView.tsx`)**: Glowing double-stroke polyline routes connecting daily stops sequentially (Stop 1 → Stop 2 → Stop 3) with dynamic bounds auto-fitting.

### Phase 7 — UI Polish, Timeline, Drag-and-Drop & Real-World Utilities (100% ✅)
45. **Dynamic LLM-Powered Clarifying Questions (`intake_agent.py`)**: 3-tier chain (curated templates -> Gemini 2.0 Flash / Groq dynamic LLM contextual questions -> static fallback) creating prompt-specific preference chips.
46. **Concrete Time-Slot Scheduling (`timeline.ts`)**: Sequential time blocks (`09:00 AM – 10:15 AM`) on StopCards + view mode switcher (Cards View 🗂️ vs Timeline View ⏱️).
47. **Drag-and-Drop Stop Reordering (`ItineraryView.tsx` & `main.py`)**: Interactive handles `⋮⋮` with client-side Haversine transit time recalculation + `POST /plan/{id}/reorder` persistence.
48. **Skeleton Shimmer Loading States (`globals.css`)**: 3-card pulsing skeleton placeholders during SSE generation.
49. **React Error Boundaries & SSE Watchdog (`ErrorBoundary.tsx` & `ChatPanel.tsx`)**: Safe error containment and 45s connection watchdog with retry banner.
50. **User Feedback Thumbs Loop (`feedback_store.py`)**: 👍 / 👎 buttons per stop recording to SQLite and `backend/data/user_feedback.jsonl` for model calibration.
51. **Smart Weather-Aware Packing Checklist (`packing_list_generator.py` & `PackingListModal.tsx`)**: Activity- and climate-aware packing checklist with interactive checkboxes, progress bar, and clipboard copy.
52. **iCalendar (.ics) Export Service (`ical_generator.py`)**: RFC 5545 calendar export with direct download in `ItineraryView` & `ShareModal`.
53. **Google Maps Navigation Deep Links**: 1-click turn-by-turn walking navigation links on every StopCard.
54. **Dietary Filter Chips**: Vegan, Halal, Vegetarian, Gluten-Free, and Jain dietary preference chips in Studio.
55. **36/36 Unit Tests Passing**: Full backend test suite passing in pytest.
56. **Clean Next.js Production Build**: 0 TypeScript / Turbopack errors.

---

## Status & System Readiness

All core WanderAI developmental phases (Phases 0 through 7) are **100% completed, verified with 36/36 unit tests, and production-ready**!

---

## Reference Documents
- [`docs/COMPREHENSIVE_AUDIT_AND_ROADMAP.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/docs/COMPREHENSIVE_AUDIT_AND_ROADMAP.md) — Comprehensive architectural analysis & roadmap.
- [`docs/IMAGE_INTEGRATION.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/docs/IMAGE_INTEGRATION.md) — Full image implementation spec (4-tier Wikipedia cascade, frontend changes, schema updates).
- [`docs/TROUBLESHOOTING_AND_MISTAKES.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/docs/TROUBLESHOOTING_AND_MISTAKES.md) — Persistent log of 12 known pitfalls, model quirks, and rules for what NOT to do.
- [`.context/PROJECT_CONTEXT.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/.context/PROJECT_CONTEXT.md) — Architecture, active model names, Chroma path, coding conventions.
- [`.context/TASKS.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/.context/TASKS.md) — Granular phase task checklist.
- [`.context/HANDOFF.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/.context/HANDOFF.md) — Latest session bug fixes & immediate next steps.

