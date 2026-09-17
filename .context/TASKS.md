# TASKS.md — Project Roadmap & Task Checklist
> Last updated: 2026-09-16

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

## Phase 5: Local Fine-Tuned Narration Model (LoRA) (COMPLETED ✅)
- [x] **Dataset curation (`ml/curate_dataset.py`)**: 320 diverse atmospheric travel writing samples exported to `ml/dataset/train.jsonl` (288) and `ml/dataset/eval.jsonl` (32)
- [x] **LoRA training pipeline (`ml/train_lora.py`)**: Unsloth + PEFT + TRL script for Llama 3.2 3B Instruct (4-bit QLoRA, rank=16, alpha=32, cosine scheduler, GGUF export)
- [x] **Google Colab Training Notebook (`ml/train_colab_notebook.ipynb`)**: Runnable single-click notebook for Colab T4 GPU
- [x] **Ollama Modelfile (`ml/Modelfile`)**: Configured model definition with temperature=0.4 and anti-cliché system prompt
- [x] **Local Ollama Narrator Tool (`backend/app/tools/ollama_narrator.py`)**: Zero-latency local client integrated into `planner_agent.py` and `editor_agent.py` with automatic fallback
- [x] **Automated & Qualitative Evaluation (`ml/eval_narrator.py` & `docs/eval_results.md`)**: 10-landmark benchmark evaluation demonstrating 88.0/100 score and 0% cliché frequency
- [x] **24/24 unit tests passing** in pytest suite (`test_ollama_narrator.py`, `test_history_store.py`, `test_editor_agent.py`, `test_scoring.py`)
- [x] **Next.js frontend build** compiling cleanly with zero TypeScript errors

---

## Phase 6: Export, Sharing & Production Polish (COMPLETED ✅)
- [x] **Headless Playwright PDF export (`backend/app/tools/pdf_generator.py`)**:
  - [x] Print-optimized HTML generator with Google Fonts (`Outfit`, `Playfair Display`), cover banners, day themes, weather forecasts, numbered stop cards, real photos, durations, costs, and atmospheric narrations
  - [x] Playwright Chromium converter generating A4 PDF brochures with `print_background=True`
  - [x] `GET /export/pdf/{itinerary_id}` for saved trips and `POST /export/pdf` for immediate in-memory export
- [x] **Shareable public itinerary URLs (`frontend/src/app/trip/[slug]/page.tsx`)**:
  - [x] Standalone read-only public trip page with responsive layout, day switcher tabs, MapView with route lines, and StopCard lists
  - [x] Backend `GET /share/{slug_or_id}` endpoint retrieving saved itineraries
  - [x] "✨ Plan Your Own Trip" CTA header button linking to `/`
- [x] **Interactive Share Modal (`frontend/src/components/ShareModal.tsx`)**:
  - [x] 1-click Copy Public Share Link with instant "✅ Copied!" feedback
  - [x] Direct WhatsApp, X (Twitter), and Email share integrations
  - [x] PDF download shortcut inside modal
- [x] **Sequential Leaflet Route Overlays (`frontend/src/components/MapView.tsx`)**:
  - [x] Dual-layer glowing route polyline connecting daily stops sequentially (Stop 1 → Stop 2 → Stop 3)
  - [x] Auto-fit map bounds dynamically accommodating both marker pins and route paths
- [x] **31/31 unit tests passing** in pytest suite (`test_export_and_share.py`, `test_ollama_narrator.py`, `test_history_store.py`, `test_editor_agent.py`, `test_scoring.py`)
- [x] **Next.js production build** compiling with 0 TypeScript / Turbopack errors and `/trip/[slug]` dynamic route

---

## Phase 7: Bug Fixes, Dynamic Clarifications & Polish (COMPLETED ✅)

### 7A — Critical Bug Fixes (COMPLETED ✅)
- [x] **Quick-edit chips no longer treat instruction as a new trip**:
  - Root cause: `onQuickEdit` was routing through `externalPrompt` → `handleSend()` with no action context, causing backend to run full planner from scratch with unrelated results
  - Fix: Added `externalEditInstruction` prop to `ChatPanel`; triggers `handleSend(instruction, { action: 'edit_whole' })` which sends `existing_itinerary_id` to backend
  - Updated `page.tsx` to wire `ItineraryView.onQuickEdit` → `setExternalEditInstruction` (was `setExternalPrompt`)
- [x] **Leaflet route polyline crash fixed** (`TypeError: Cannot read properties of undefined (reading 'x')`):
  - Root cause: Polylines were drawn synchronously before `invalidateSize()` settled the map container's pixel projection
  - Fix: Moved polyline construction inside the `setTimeout(50ms)` block alongside `invalidateSize()` in `MapView.tsx`

### 7B — Dynamic LLM-Powered Clarification Questions (COMPLETED ✅)
- [x] **Problem**: Clarification preference chips were fixed/hardcoded — same generic options (travel_style, pace) appeared for every prompt regardless of what the user mentioned
  - E.g. "3 days in Kyoto, anime and gaming culture" showed identical chips as "3 days in Kyoto, Zen temples and ramen"
- [x] **Solution**: `_generate_dynamic_clarification_questions()` in `intake_agent.py`:
  - Uses Gemini 2.0 Flash (primary) / Groq Llama 3.1 8B (fallback) to generate 2–3 questions contextual to the *actual* user prompt
  - Questions and chip labels are now specific to what the user mentioned (vibe, interest area, cuisine type, region)
  - Falls back to static `DESTINATION_QUESTIONS` template (for known cities: Goa, Mumbai, Lisbon, Rajasthan, etc.) then generic 2-question set if LLM unavailable
- [x] Architecture: `CLARIFICATION_SYSTEM_PROMPT` instructs LLM to generate JSON matching `ClarificationQuestion` schema; response parsed with regex + `json.loads`; full Gemini → Groq → static fallback chain

### 7C — UI Polish, Timeline & Real-World Utilities (COMPLETED ✅)
- [x] **Concrete time-slot scheduling (09:00 AM – 10:15 AM style per stop)**:
  - `calculateDayTimeline()` in `timeline.ts` calculates precise sequential time blocks taking into account stop durations and transit times
  - Rendered with clock badge `🕒 09:30 AM – 11:00 AM` on each StopCard
  - View switcher: **Cards View** 🗂️ vs **Timeline View** ⏱️
- [x] **Drag-and-drop stop reordering with auto-transit recalculation**:
  - Interactive grip handles `⋮⋮` on StopCards with drag-and-drop support
  - On drop, client optimistically recalculates Haversine distance and transit times (`recalculateSequentialTransit`), updating timeline slots immediately
  - Syncs to backend `POST /plan/{itinerary_id}/reorder` and `localStorage`
- [x] **Skeleton shimmer loading states during SSE generation**:
  - Replaced spinner with 3-card glowing skeleton placeholder and animated map radar preview
- [x] **React error boundaries & SSE timeout watchdog**:
  - `ErrorBoundary.tsx` component wrapping Studio and Itinerary workspaces
  - 45s safety watchdog in `ChatPanel.tsx` with retry alert banner
- [x] **Illustrated empty state UI for history panel**:
  - Themed empty state with floating compass emblem, description, and "✨ Plan Your First Journey" CTA button
- [x] **User feedback thumbs (👍/👎 per stop) loop**:
  - Thumbs up/down buttons on each StopCard
  - `POST /feedback` endpoint saving to SQLite `stop_feedback` table and appending to `backend/data/user_feedback.jsonl` for LoRA model tuning
- [x] **Dietary filter chips**:
  - Added filter bar (🌱 Vegan, 🕌 Halal, 🥗 Vegetarian, 🌾 Gluten-Free, 🕊️ Jain) in `ChatPanel.tsx`
- [x] **Smart weather-aware packing list generator**:
  - `POST /trip/packing-list` & `POST /trip/{itinerary_id}/packing-list` using LLM (Gemini 2.0 Flash / Groq)
  - `PackingListModal.tsx` with interactive checkboxes, progress bar, category filters, and clipboard copy
- [x] **iCalendar (.ics) export**:
  - RFC 5545 `.ics` generator (`backend/app/tools/ical_generator.py`)
  - `GET /export/ical/{itinerary_id}` & `POST /export/ical` endpoints
  - Direct 1-click download buttons in `ItineraryView` header and `ShareModal`
- [x] **Google Maps navigation deep links**:
  - "🧭 Map" button on each StopCard opening walking directions in Google Maps
- [x] **36/36 unit tests passing** in pytest suite (`test_phase7_features.py`, `test_export_and_share.py`, `test_ollama_narrator.py`, `test_history_store.py`, `test_editor_agent.py`, `test_scoring.py`, `test_phase2_ranker.py`)
- [x] **Next.js production build** compiling with 0 errors

---

## Phase 8: UI/UX Design System Overhaul & Visual Polish (COMPLETED ✅)
- [x] **Aurora Animated Gradient Background**:
  - Added 3-blob dynamic ambient lighting mesh (`.aurora-blob-1`, `.aurora-blob-2`, `.aurora-blob-3`) in `globals.css` and `TravelLiveWallpaper.tsx`
  - Subtle drifting keyframe animation (`@keyframes auroraFloat`) producing living frosted-glass depth
- [x] **Vertical Full-Bleed StopCard Layout & 3D Spring Tilt Physics**:
  - Redesigned StopCard to vertical card layout with 175px photographic banner, gradient scrim, and overlaid chips
  - Interactive 3D perspective spring tilt physics tracking cursor position (`onMouseMove`)
  - Staggered cascade entrance animation (`@keyframes slideUpFade` with `:nth-child` delays)
  - Tabular mono typography (`JetBrains Mono`) for time slots, distances, durations, and costs
- [x] **Destination-Reactive Theme Engine (`destinationTheme.ts`)**:
  - Automatically classifies destination into 5 distinct archetypes:
    - 🌴 Tropical (Sunset Coral `#FF6B35` + Lagoon `#00C897`)
    - 🇵🇹 European (Warm Gold `#D4AF37` + Twilight Violet `#8B5CF6`)
    - 👑 Desert / Heritage (Dune Amber `#F4A261` + Spice Red `#E63946`)
    - 🏔️ Mountain / Alpine (Glacier Blue `#38BDF8` + Pine Green `#10B981`)
    - 🏙️ Metropolis (Golden Amber `#FFBF00` + Electric Cyan `#00DBE7`)
  - Injects dynamic CSS variables on document root upon itinerary generation or history selection
- [x] **Toast Notification System (`Toast.tsx`)**:
  - Zero-dependency floating animated toast notification manager
  - Dispatched on feedback thumbs rating, iCal download, PDF export, and share link clipboard copy
- [x] **Mobile Sticky Bottom Navigation & Swipeable Day Carousel**:
  - Sticky bottom tab navigation bar on `< 768px` viewports (`[💬 Studio] [📋 Itinerary] [🗂️ History] [🧭 Architecture]`)
  - Touch-friendly 44×44px interactive tap targets
  - Horizontal swipeable day tabs with CSS `scroll-snap-type: x mandatory`
- [x] **Typography & Hero Visuals**:
  - Loaded Google Fonts (`JetBrains Mono`, `Outfit`, `Playfair Display`, `Sora`)
  - Luminous gradient text (`.gradient-text-hero`) on hero headlines
  - Animated live count-up for trip total cost estimates

---

## Phase 9: Anti-AI-Look Overhaul, Model Upgrades & Map/Image Hardening (COMPLETED ✅)

### 9A — Anti-AI-Look Visual Polish (`docs/ANTI_AI_LOOK_PLAN.md`)
- [x] **Restored Center-Aligned Hero Layout (`R1`)**:
  - Centered headline (`.hero-title`), subtitle (`.hero-subtitle`), and action CTA group (`.hero-actions`) in `page.tsx`
  - Visually anchored by the curated destination photo cards below
- [x] **Sleek 12px Button Border Radius (`R2`)**:
  - Replaced boxy 8px borders on `.btn-primary`, `.btn-secondary`, and `.nav-cta` with 12px (`var(--radius-md)`) in `globals.css`
  - Eliminates the generic pill look without sacrificing tactile elegance
- [x] **Clearer, Action-Driven Intro Badge (`A1`)**:
  - Updated intro pill text to `✦ DESCRIBE YOUR TRIP · AI BUILDS THE REST`
- [x] **Functional Header Badge (`A2`)**:
  - Replaced generic "Multi-Agent Swarm" with `Live · 6 Agents`
- [x] **Friendly Mobile Navigation Tab Label (`A3`)**:
  - Renamed tab 4 from "Architecture" to `How It Works` for intuitive mobile navigation

### 9B — 2026 Model Migrations & Resilience
- [x] **Sunsetting Deprecated Models**:
  - Removed sunset models returning 404 (`gemini-2.5-flash`, `gemini-2.0-flash`, Groq `llama-3.1-8b-instant`, `llama-3.3-70b-versatile`, `qwen/qwen3.6-27b`)
  - Standardized all agents on **`gemini-3.6-flash`** (primary) with fallback to `gemini-3.5-flash`
  - Upgraded Groq model to **`openai/gpt-oss-20b`** (primary) with fallback to `openai/gpt-oss-120b` across `intake_agent.py`, `planner_agent.py`, `editor_agent.py`, `packing_list_generator.py`, and `niche_scraper.py`
- [x] **Planner Agent Narration Fallback & Enrichment**:
  - Implemented Groq `openai/gpt-oss-20b` fallback in `planner_agent.py` for day themes and stop narrations when Gemini quotas exhaust (429/404)
  - Enhanced category-aware contextual fallbacks for viewpoints, museums, restaurants, markets, and historic sights

### 9C — Leaflet Map Reactivity & Render Fixes
- [x] **Preloaded Leaflet Stylesheet**:
  - Injected `leaflet@1.9.4/dist/leaflet.css` directly into `layout.tsx` `<head>` to prevent unstyled tile flash
- [x] **Eliminated Stale Closure**:
  - Routed stop marker generation through `stopsRef.current` in `MapView.tsx`, ensuring map re-renders always receive the latest itinerary stops
- [x] **Clean Container Destruction & Reinitialization**:
  - Safely cleared `(container as any)._leaflet_id` before instantiating Leaflet map, preventing `Error: Map container is already initialized` crashes
- [x] **Dynamic Destination Auto-Centering**:
  - Auto-centers map directly on the first valid stop coordinates instead of remaining frozen on default Pune coordinates

### 9D — Image Pipeline Hardening & Two-Tier Fallbacks
- [x] **Removed Failing Google Places Legacy Photo URLs**:
  - Eliminated legacy photo URLs returning `403 Forbidden` in browser `<img>` tags
  - Routed image discovery through Wikipedia REST, OpenSearch, and Wikimedia Commons cascades
- [x] **Bumped Cache to `v8`**:
  - Auto-invalidated stale or broken image URLs in `places_tool.py`
- [x] **Expanded High-Resolution Destination Banners**:
  - Added curated photography for Hyderabad, Chennai, Kolkata, Amritsar, Ahmedabad, Kochi, Shimla, Hampi, Mysore, Pondicherry, Ooty, Srinagar, Jodhpur, Jaisalmer, Seoul, Amsterdam, Prague, Vienna, Istanbul, Cairo, and Sydney in `destination_images.py`
- [x] **Two-Tier StopCard Image Fallback**:
  - Added automatic fallback to curated category photography when a landmark photo URL fails to load, with emoji fallback as final safeguard

---

## Phase 10: Performance Overhaul & Multi-Tier Photo Engine (COMPLETED ✅)

### 10A — Watchdog Timeout & Google Places Bypass
- [x] **Extend Frontend Watchdog**: Increased `ChatPanel.tsx` abort timer from 45s to 90s to eliminate false timeout errors during cold multi-agent runs
- [x] **Google Places Probe Bypass**: Probe Google Places API key once; if unauthorized or empty, short-circuit and skip the 40-request `nearbysearch` loop, cutting backend generation latency by 15–20 seconds

### 10B — Niche Scraper Bug Fix & Kashmir Support
- [x] **Fix `NameError: scored_candidates`**: Declared `scored_candidates: list[dict] = []` in `niche_scraper.py`
- [x] **Curate Kashmir Hidden Gems**: Added authentic spots (Dal Lake Shikara sunrise, Pari Mahal, Ahdoos Wazwan, Betaab Valley, Zaina Kadal artisan bazaar, Apharwat Peak)

### 10C — Diverse Category Photo Pools & Destination Libraries
- [x] **Multi-Photo Category Pools**: Replaced single static category URLs with pools of 8–10 distinct high-resolution Unsplash photos per category in `destination_images.py`
- [x] **Deterministic Photo Hashing**: Use `pool[abs(hash(name)) % len(pool)]` so cards with the same category receive completely unique, diverse photos
- [x] **Destination-Specific Photo Libraries**: Added tailored photo collections for Kashmir, Goa, Mumbai, Delhi, Jaipur, Kerala, Manali, Ladakh, Bali, Lisbon, Tokyo, Paris, Rome
- [x] **Frontend Fallback Mirror**: Updated `ItineraryView.tsx` `CATEGORY_FALLBACK_POOLS` with matching multi-photo hash selection on image error

### 10D — Regional Geocoding & Subzones for Mountain/Regional Trips
- [x] **Fix Kashmir Barmer-Desert Misgeocoding**: Added fast-path geocoding overrides for Kashmir, Srinagar, Ladakh, Manali, Himachal in `places_tool.py`
- [x] **Add Kashmir to `REGIONAL_SUBZONES`**: Subzones for Srinagar, Gulmarg, Pahalgam, and Sonamarg for day-by-day valley dispersion

### 10E — Cache Integrity & Cache Bump to `v9`
- [x] **Prevent Mock Stop Caching**: Mark mock fallback stops as `source="mock"` so they are never written to Chroma as real `opentripmap` stops
- [x] **Bump Cache to `v9`**: Auto-flush poisoned Barmer-desert Kashmir cache entries and refresh with genuine regional attractions

---

## Phase 11: Dual-Mode Intake & Multi-Select Planning Studio (COMPLETED ✅)

### 11A — Mode Switcher & UI Framework
- [x] **Top Mode Segmented Control**: Implement a sleek segmented toggle (`💬 Freeform Chat` vs `✨ Guided Builder`) at the top of `ChatPanel.tsx` with animated active indicator and Nocturnal Voyager glass styling.
- [x] **Bi-Directional State Preservation**: Ensure destination, duration, selected styles, and dietary preferences persist when toggling between Freeform Chat and Guided Builder.

### 11B — Structured / Guided Builder View
- [x] **Visual Trip Configuration Panel**: Build interactive configuration controls in `ChatPanel.tsx` replacing/overlaying the chat scroll area when in Guided mode.
- [x] **Destination Input & Popular Chips**: Text input for custom destination + quick-select chips (Goa, Mumbai, Rajasthan, Lisbon, Kyoto, Kashmir, Paris).
- [x] **Visual Duration Selector**: Interactive day pills (1, 2, 3, 4, 5, 7, 10 days).
- [x] **Multi-Select Travel Style / Vibe**: Multi-choice chips with icons (Iconic Landmarks 🏛️, Hidden Gems 💎, Cultural Heritage 🏰, Foodie & Markets 🍲, Scenic Nature 🌿, Adventure 🏄, Relaxed Leisure 🧘).
- [x] **Daily Pacing Selector**: Single-select pills (Relaxed 2-3 stops 🧘, Moderate 4-5 stops ⚡, Packed 6+ stops 🏃).
- [x] **Budget Tier & Companions**: Segmented chips for budget (Budget 🪙, Mid-Range ⚖️, Luxury ✨) and group (Solo 🎒, Couple 💑, Family 👨‍👩‍👧, Friends 👥).
- [x] **Multi-Select Must-Have Activities / Interests**: Multi-choice pills (Photo spots 📸, Cafes ☕, Beaches 🏖️, Bazaars 🛍️, Sunsets 🌄, Art/Museums 🎨, Street Food Trails 🍜).
- [x] **Multi-Select Dietary Bias**: Integrated filter chips (Vegan 🌱, Vegetarian 🥗, Halal 🕌, Gluten-Free 🌾, Jain 🕊️).
- [x] **Live Summary & Plan CTA**: Real-time summary strip with `🚀 Generate Custom Itinerary` and `↺ Reset` actions.

### 11C — Multi-Select Clarification Engine (COMPLETED ✅)
- [x] **Schema & Type Updates**: Added `is_multi_select: bool = False` to `ClarificationQuestion` in `schemas.py` and `types/index.ts`.
- [x] **Multi-Select Answer State**: Updated `selectedAnswers` state in `ChatPanel.tsx` to `Record<string, string[]>` with toggle click behavior, active check indicators (`✓`), and `(Multi-select)` label badge.
- [x] **Backend Multi-Select Parsing**: Updated `ChatRequest.answers` to `Optional[dict[str, Any]]` and updated `intake_agent.py` to parse lists for `travel_style` (blending `niche` + `popular` to 50/50 balanced), `region_vibe`, `interests`, `activity`, and `dietary`. Verified with 3 new automated tests.

### 11D — Strategic Fixed-Info Retrieval in Freeform Chat (COMPLETED ✅)
- [x] **Strategic Dimension Tracking**: Modified `intake_agent.py` to track 6 key dimensions (destination, duration, travel style/interests, pace, budget, group). Partially specified prompts trigger contextual questions, while rich prompts bypass clarification.
- [x] **Contextual Follow-up Questions**: When prompt is partial or destination is missing, generates strategic clarification questions addressing missing dimensions with multi-select enabled.
- [x] **Expanded Question Templates**: Enriched `DESTINATION_QUESTIONS` for Goa, Mumbai, Pune, Rajasthan, Kashmir, and Lisbon with 3–4 questions and 4–5 multi-select options each. Upgraded dynamic LLM generator and generic fallback questions. Verified with 7 automated tests.

### 11E — Instant "⚡ Generate Trip with Given Info" Action (COMPLETED ✅)
- [x] **Clarification Card Instant Button**: Added "⚡ Generate Trip with Given Info (Defaults)" button inside clarification messages.
- [x] **Persistent Chat Action Bar**: Rendered a prominent "⚡ Generate Trip with Given Info for [Destination] [N Days]" bar above the chat input whenever a destination has been detected or entered.
- [x] **One-Click Force Plan**: Triggers immediate itinerary generation with `forcePlan: true`, passing any selected clarification answers, destination, and duration without requiring further clarification rounds.
