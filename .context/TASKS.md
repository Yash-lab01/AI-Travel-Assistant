# TASKS.md — Project Roadmap & Task Checklist

## Phase 0: Foundations & Architecture
- [x] FastAPI backend setup with `/plan` (REST), `/plan/stream` (SSE), and `/health` endpoints
- [x] LangGraph `StateGraph` skeleton with SQLite checkpointer (`data/checkpoints.db`)
- [x] Complete Pydantic schemas (`TripRequest`, `Stop`, `DayPlan`, `Itinerary`, `NicheScore`, `AgentEvent`)
- [x] Embedded ChromaDB vector store initialization (`niche_spots` + `itinerary_cache`)
- [x] Log-normalized hidden gem score formula (`compute_hidden_gem_score`)
- [x] Unit test suite for scoring formula (7/7 tests passing in `test_scoring.py`)
- [x] Next.js 16 frontend setup with TypeScript, SSE stream reader, and App Router
- [x] "Nocturnal Voyager" dark glassmorphic design system tokens in `globals.css`

---

## Phase 1: Real Data Pipeline & Spatial Clustering
- [x] **Intake Agent** (`intake_agent.py`):
  - [x] Groq Llama 3.1 8B structured JSON slot extraction
  - [x] Regex rule-based fallback parser (zero-key mode)
- [x] **Places Tool** (`places_tool.py`):
  - [x] Nominatim OpenStreetMap city geocoding (free, no key)
  - [x] OpenTripMap API attraction discovery
  - [x] Google Places API enrichment (photos, ratings, review counts)
  - [x] ChromaDB destination cache integration
- [x] **Planner Agent** (`planner_agent.py`):
  - [x] Pure-Python k-means spatial clustering (groups stops by geographic proximity)
  - [x] Gemini 2.5 Flash day themes & per-stop narrations with heuristic fallback
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
  - [x] Added Indian travel hubs (Delhi, Mumbai, Jaipur, Goa, Bengaluru) and curated journeys

---

## Phase 2: Niche Signal Scraping & Scoring Engine (COMPLETED)
- [x] **Tavily Search Tool** (`backend/app/tools/tavily_tool.py`):
  - [x] Query travel blogs & Reddit discussions using `TAVILY_API_KEY`
  - [x] Extract place snippets, URLs, and source attributions with rich mock fallbacks
- [x] **Reddit Public Scraper Tool** (`backend/app/tools/reddit_tool.py`):
  - [x] Query Reddit public JSON search API with custom `User-Agent` (zero auth/zero key requirement)
  - [x] Extract post titles, selftext snippets, and community upvote metrics
- [x] **Niche Extractor & Sentiment Pipeline** (`backend/app/tools/niche_scraper.py`):
  - [x] LLM structured extraction (Groq/Gemini) + curated fallback candidates
  - [x] VADER sentiment intensity analysis on extracted mention contexts
  - [x] Log-normalized hidden gem score calculation via `compute_hidden_gem_score`
  - [x] ChromaDB caching in `niche_spots` collection
- [x] **Ranker Agent** (`backend/app/agents/ranker_agent.py`):
  - [x] Wire ranker node into LangGraph: `intake -> ranker -> planner -> END`
  - [x] Blends mainstream OpenTripMap attractions with niche-scored spots by `niche_weight`
  - [x] Pace-aware stop selection and category diversity
- [x] **Test Suite Verification**:
  - [x] 11/11 tests passing in pytest (`test_scoring.py` + `test_phase2_ranker.py`)
  - [x] Tested on Lisbon and Rajasthan queries (verified `is_niche=True` and scores attached)

---

## Phase 3: Routing, Weather & Progressive Streaming (NEXT)
- [ ] **OpenRouteService Integration** (`routing_tool.py`): Calculate walking & transit travel times between sequential stops
- [ ] **Open-Meteo Integration** (`weather_tool.py`): Free daily weather forecasts attached to `DayPlan.weather_note`
- [ ] **Budget & Cost Engine**: Dynamic daily spend tracking against `TripRequest.budget_usd`
- [ ] **Progressive Day Streaming**: Stream each `day_ready` event over SSE so days render progressively in the UI

---

## Phase 4: Local Fine-Tuned Narration Model (LoRA)
- [ ] **Dataset Curation** (`backend/finetuning/curate_dataset.py`): CC-licensed travel writing
- [ ] **LoRA Training** (`backend/finetuning/train_lora.py`): Unsloth + PEFT on Llama 3.2 3B (Colab T4)
- [ ] **Ollama Deployment**: Local GGUF serving via `ChatOllama(model="travel-narrator-lora")`
- [ ] **Blind Evaluation**: Documented before/after comparison in `eval_results.md`

---

## Phase 5: Multi-Turn Conversational Editing
- [ ] Multi-turn intent classifier (new trip vs edit stop vs adjust pace vs change budget)
- [ ] LangGraph state checkpoint time-travel recovery
- [ ] UI follow-up quick action prompts ("swap stop", "more relaxed pace")

---

## Phase 6: Export, Sharing & Production Polish
- [ ] Headless Playwright PDF export endpoint (`/export/pdf/{itinerary_id}`)
- [ ] Shareable public itinerary URL slugs (`/trip/{slug}`)
- [ ] Leaflet polyline route overlay connecting stops sequentially
