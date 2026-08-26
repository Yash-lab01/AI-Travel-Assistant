# TASKS.md — Project Roadmap & Task Checklist
> Last updated: 2026-08-25

## Phase 0: Foundations & Architecture (COMPLETED ✅)
- [x] FastAPI backend setup with `/plan` (REST), `/plan/stream` (SSE), and `/health` endpoints
- [x] LangGraph `StateGraph` skeleton with SQLite checkpointer (`data/checkpoints.db`)
- [x] Complete Pydantic schemas (`TripRequest`, `Stop`, `DayPlan`, `Itinerary`, `NicheScore`, `AgentEvent`)
- [x] Embedded ChromaDB vector store initialization (`niche_spots` + `itineraries`)
- [x] Log-normalized hidden gem score formula (`compute_hidden_gem_score`)
- [x] Unit test suite for scoring formula (7/7 tests passing in `test_scoring.py`)
- [x] Next.js 16 frontend setup with TypeScript, SSE stream reader, and App Router
- [x] "Nocturnal Voyager" dark glassmorphic design system tokens in `globals.css`

---

## Phase 1: Real Data Pipeline & Spatial Clustering (COMPLETED ✅)
- [x] **Intake Agent** (`intake_agent.py`):
  - [x] Gemini 3.5 Flash / Groq structured JSON slot extraction
  - [x] Regex rule-based fallback parser (zero-key mode)
- [x] **Places Tool** (`places_tool.py`):
  - [x] Nominatim OpenStreetMap city geocoding (free, no key)
  - [x] OpenTripMap flat JSON parser for real attractions (fixed GeoJSON assumption bug)
  - [x] Google Places API enrichment (photos, ratings, review counts)
  - [x] Versioned ChromaDB cache (`CACHE_VERSION="v6"`) — only `source="opentripmap"` stops stored
- [x] **Planner Agent** (`planner_agent.py`):
  - [x] **K-means++ clustering** (maximally spread centroids, prevents Day 1 underpopulation)
  - [x] Post-clustering rebalance pass to distribute stops evenly across days
  - [x] Gemini 3.5 Flash day themes with code-fence stripping + destination-aware fallbacks
  - [x] Per-stop narrations with `safe_extract_text`
  - [x] Pace-aware stop counts (slow=3, moderate=5, fast=7)
- [x] **Frontend Overhaul**:
  - [x] Multi-section scrollable landing page with sticky navbar & footer
  - [x] High-impact hero section with display typography & prompt quick-start cards
  - [x] Architecture & feature showcase cards
  - [x] Interactive Planning Studio dual-panel workspace (`ChatPanel` + `ItineraryView`)
  - [x] HTML5 Canvas Travel Live Wallpaper with flight arcs & Indian hubs
  - [x] Leaflet + CartoDB Dark Matter map integration (zero credit card / zero token requirement)
- [x] **Versatile Positioning**:
  - [x] Updated UI, prompt chips, and documentation to support both iconic sights & hidden gems
  - [x] Added Indian travel hubs (Delhi, Mumbai, Jaipur, Goa, Pune, Bengaluru) and curated journeys

---

## Phase 2: Niche Signal Scraping & Scoring Engine (COMPLETED ✅)
- [x] **Tavily Search Tool** (`backend/app/tools/tavily_tool.py`):
  - [x] Query travel blogs & Reddit discussions using `TAVILY_API_KEY`
  - [x] Extract place snippets, URLs, and source attributions with rich mock fallbacks
- [x] **Reddit Public Scraper Tool** (`backend/app/tools/reddit_tool.py`):
  - [x] Query Reddit public JSON search API with custom `User-Agent` (zero auth/zero key requirement)
  - [x] Extract post titles, selftext snippets, and community upvote metrics
- [x] **Niche Extractor & Sentiment Pipeline** (`backend/app/tools/niche_scraper.py`):
  - [x] LLM structured extraction (Groq/Gemini) + curated authentic candidates per city
  - [x] VADER sentiment intensity analysis on extracted mention contexts
  - [x] Log-normalized hidden gem score calculation via `compute_hidden_gem_score`
  - [x] ChromaDB caching in `niche_spots` collection
- [x] **Ranker Agent** (`backend/app/agents/ranker_agent.py`):
  - [x] Wire ranker node into LangGraph: `intake -> ranker -> planner -> END`
  - [x] Blends mainstream OpenTripMap attractions with niche-scored spots by `niche_weight`
  - [x] **Guaranteed non-empty `ranked_stops` output** — planner never bypasses ranker
  - [x] Pace-aware stop selection and category diversity
- [x] **Test Suite Verification**:
  - [x] 11/11 tests passing in pytest (`test_scoring.py` + `test_phase2_ranker.py`)

---

## Phase 3: Conversational Intake, Regional Spatial Dispersion & UI Overhaul (COMPLETED ✅)
- [x] **Conversational Intake with Clarifying Questions** (`intake_agent.py`):
  - [x] Detect underspecified prompts (e.g. *"3 day trip in Goa"*)
  - [x] Generate 2–3 contextual clarifying questions with interactive quick-reply chips
  - [x] Provide 1-click **"Plan with defaults now"** bypass option
  - [x] Destination persistence across clarification turns
- [x] **Regional Multi-Zone Discovery & Spatial Dispersion** (`places_tool.py`):
  - [x] State/region awareness for wide destinations (Goa, Rajasthan, Bali, Kerala, Mumbai, Pune, Delhi, Jaipur, Tokyo, Lisbon)
  - [x] Multi-centroid / adaptive radius discovery to eliminate 6km micro-clustering
  - [x] K-means++ assigns geographically distinct sub-regions per day with balanced stop counts
- [x] **Routing & Weather Tools**:
  - [x] `routing_tool.py`: Calculate realistic walking & transit minutes between consecutive stops
  - [x] `weather_tool.py`: Open-Meteo daily weather forecast attached to `DayPlan.weather_note`
- [x] **Smart Currency Formatter** (`currency.ts`):
  - [x] Indian trips formatted in `₹ INR` (e.g. ₹1,200 / ₹4,500), international in `$ USD`
- [x] **Centered Studio UI & Wide Side-by-Side Map/Timeline Layout** (`page.tsx`, `ChatPanel.tsx`, `ItineraryView.tsx`, `MapView.tsx`, `globals.css`):
  - [x] Large prominent centered conversational studio hub
  - [x] Expansive side-by-side Map + Day-by-Day Timeline workspace below chat
  - [x] Safe day tab indexing and error-proof Leaflet bounds handling
- [x] **Phase 3 Hardening Pass** (Bug Fixes):
  - [x] K-means++ replaces index-seeded k-means for balanced Day 1/2/3 stop counts
  - [x] Versioned Chroma cache (currently **v6**) auto-invalidates stale/mock entries
  - [x] Ranker guaranteed non-empty output; planner `[WARNING]` on bypass
  - [x] Gemini code-fence stripping for reliable theme JSON parsing
  - [x] Destination-aware fallback themes for all major Indian cities + Bali/Lisbon/Tokyo
  - [x] Mock places ONLY used when `OTM_KEY` is entirely absent (wider-radius retry added)

---

## Phase 4: Image Integration, Visual Richness & UX Fixes (COMPLETED ✅)

> Full design spec: [`docs/IMAGE_INTEGRATION.md`](../docs/IMAGE_INTEGRATION.md)

Images are fully integrated across the app with zero-key fallback compatibility:

### 4a — Backend: Image Sourcing (COMPLETED ✅)
- [x] **`backend/app/tools/destination_images.py`** — curated high-res Unsplash photo map for 25+ Indian & global destinations (Mumbai, Goa, Delhi, Jaipur, Kerala, Pune, Bali, Lisbon, Tokyo, Paris, Rome, Barcelona, Kyoto, etc.)
- [x] **`places_tool.py` — 3-tier Wikipedia image cascade** — `fetch_wikimedia_image(place_name, destination)` tries:
  1. Wikipedia REST Summary API (instant exact article lead photo)
  2. Wikipedia Generator Search with `pageimages` (fuzzy title matching)
  3. Wikimedia Commons file search (CC-licensed community photography)
  - Achieves ~100% real image match rate for major landmarks; zero auth required
- [x] **`places_tool.py` — Category fallback** — `_unsplash_fallback_url()` wraps `get_category_fallback_image()` for stops where Wikipedia also misses
- [x] **Enrich ALL stops** — `enrich_with_google_places()` enriches all unique attractions with photos & ratings
### 4a — Backend Image Sourcing (COMPLETED ✅)
- [x] **`destination_images.py`** — curated landscape hero banners (25+ destinations)
- [x] **`places_tool.py` — OpenSearch + PageImages 4-tier real image cascade**:
  - Tier 1: Wikipedia REST Summary API
  - Tier 2: Wikipedia OpenSearch API (canonical article discovery -> lead photo)
  - Tier 3: Wikipedia Generator Search with PageImages
  - Tier 4: Wikimedia Commons direct search
- [x] **`places_tool.py` — Cache bumped to `v7`** to auto-refresh all destinations with real high-resolution landmark photography

### 4b — Frontend Visual Components (COMPLETED ✅)
- [x] **`ItineraryView.tsx` — Visual Day Banners & Itinerary Cover**
- [x] **`ItineraryView.tsx` — StopCard photographic thumbnails** with shimmer skeleton & lazy loading
- [x] **`globals.css`** — `.day-banner-card`, `.stop-card-image-wrap`, `@keyframes shimmer`, `.itinerary-cover-banner`
- [x] **`MapView.tsx` — Leaflet popup photo thumbnails** — embeds 100px photo inside popup when a map marker is clicked

### 4c — Landing Page Destination Cards & 100vh Intro Screen (COMPLETED ✅)
- [x] **`page.tsx` — 100vh Minimalist Brand Intro Screen (`#intro`)** — grand display typography, floating emblem glow, and animated "Scroll to explore ↓" button
- [x] **`page.tsx` — Detailed Overview Section (`#overview`)** — headline, description lines, CTA buttons, curated photographic cards for Goa, Rajasthan, Lisbon, Kyoto, and live stats strip
- [x] **`globals.css`** — `.intro-hero-screen`, `.intro-brand-title`, `.intro-scroll-arrow` bounce animation, and photographic prompt cards

### 4d — UX Bug Fixes (COMPLETED ✅)
- [x] **`MapView.tsx`** — Leaflet `fitBounds` error fixed: `invalidateSize()` + 50ms defer + identical-coord setView fallback
- [x] **`AgentEventFeed.tsx` + `ChatPanel.tsx`** — replaced global `scrollIntoView()` with internal container `scrollTop` to prevent viewport jump on page load
- [x] **`page.tsx`** — `window.history.scrollRestoration = 'manual'` + `window.scrollTo(0,0)` on mount so page always starts at the brand intro section

---

## Phase 4e: Multi-Turn Conversational Editing & State Iteration (COMPLETED ✅)
- [x] Multi-turn intent classifier node (`classify_edit_intent` in `intake_agent.py` identifying `new_trip` | `swap_stop` | `remove_stop` | `adjust_pace` | `change_budget` | `tell_me_more`)
- [x] **`editor_agent.py`** — dedicated LangGraph Editor Agent node for targeted state patching:
  - [x] `swap_stop`: non-duplicate candidate search, category matching, 3-tier Wikipedia photo resolution, and narration generation
  - [x] `remove_stop`: stop deletion from specific day
  - [x] Transit time recalculation via `calculate_sequential_transit_times`
  - [x] Cost recalculation for updated days and whole trip
  - [x] `tell_me_more`: comprehensive insider guides & photo spots without altering itinerary
  - [x] `adjust_pace`: relaxed / active daily density adjustment
- [x] **LangGraph State Machine** — conditional routing in `travel_graph.py`: `intake -> editor -> END` for edits, preserving existing itinerary context
- [x] **`PATCH /plan/{id}/stop` endpoint** in `main.py` + enhanced SSE streaming with `assistant_message` events
- [x] **UI Quick Action Controls on StopCard** (`ItineraryView.tsx`) — `🔄 Swap`, `❌ Remove`, `💬 Tell Me More`
- [x] **Quick Itinerary Adjustment Chips** (`ItineraryView.tsx`) — 🧘 Relaxed Pacing, 💎 More Hidden Gems, 🍲 Foodie & Cafes, 🌿 Scenic & Nature
- [x] **15/15 unit tests passing** in pytest suite (`test_editor_agent.py`, `test_phase2_ranker.py`, `test_scoring.py`)
- [x] **Next.js frontend build** compiling cleanly with zero TypeScript errors

---

## Phase 4f: Trip History & Saved Itinerary Browser (COMPLETED ✅)

### Backend
- [x] **`backend/app/db/history_store.py`** — SQLite `trip_history` table with `save_itinerary`, `get_all_histories`, `get_itinerary_by_id`, `delete_itinerary` helpers
- [x] **`GET /history`** in `main.py` — Returns lightweight summary list (id, destination, num_days, cover_image_url, created_at)
- [x] **`POST /history`** in `main.py` — Receives & persists full itinerary blob
- [x] **`GET /history/{id}`** in `main.py` — Returns full itinerary JSON for trip restore
- [x] **`DELETE /history/{id}`** in `main.py` — Removes a saved trip
- [x] **`backend/tests/test_history_store.py`** — 4 unit tests covering save, get_all, get_by_id, delete, and pruning (19/19 tests passing)

### Frontend
- [x] **`TripHistoryRecord` type** (`types/index.ts`) — `{ id, destination, numDays, createdAt, coverImageUrl, itinerary }`
- [x] **`frontend/src/components/TripHistoryPanel.tsx`** — Slide-in sidebar with visual trip history cards (cover photo, destination, date, num_days)
  - [x] Each card: `Load Trip` button + `Delete` trash icon
  - [x] Auto-saves every new itinerary to localStorage on SSE `itinerary` event
  - [x] Syncs to backend `POST /history` on save
  - [x] On `Load Trip`: restores itinerary into planner view and scrolls to studio
- [x] **`page.tsx`** — 🗂️ History nav link in header (badge showing count) that opens `TripHistoryPanel`
- [x] **`globals.css`** — `.trip-history-panel`, `.history-card`, `.history-card-img`, `.history-badge` styles

### Limits & Defaults
- [x] Keep last **10 trips** in `localStorage`; **50** in SQLite backend
- [x] Timestamps formatted as relative strings ("2 hours ago", "Yesterday")

---

## Phase 5: Local Fine-Tuned Narration Model (LoRA)
- [ ] Dataset curation (`curate_dataset.py`): CC-licensed travel writing
- [ ] LoRA training (`train_lora.py`): Unsloth + PEFT on Llama 3.2 3B (Colab T4)
- [ ] Local Ollama deployment: Serving via `ChatOllama(model="travel-narrator-lora")`
- [ ] Blind before/after evaluation in `eval_results.md`

---

## Phase 6: Export, Sharing & Production Polish
- [ ] Headless Playwright PDF export endpoint (`/export/pdf/{itinerary_id}`)
- [ ] Shareable public itinerary URL slugs (`/trip/{slug}`)
- [ ] Leaflet polyline route overlay connecting stops sequentially
