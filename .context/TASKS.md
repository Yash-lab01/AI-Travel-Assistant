# TASKS.md — Project Roadmap & Task Checklist

## Phase 0: Foundations & Architecture (COMPLETED)
- [x] FastAPI backend setup with `/plan` (REST), `/plan/stream` (SSE), and `/health` endpoints
- [x] LangGraph `StateGraph` skeleton with SQLite checkpointer (`data/checkpoints.db`)
- [x] Complete Pydantic schemas (`TripRequest`, `Stop`, `DayPlan`, `Itinerary`, `NicheScore`, `AgentEvent`)
- [x] Embedded ChromaDB vector store initialization (`niche_spots` + `itineraries`)
- [x] Log-normalized hidden gem score formula (`compute_hidden_gem_score`)
- [x] Unit test suite for scoring formula (7/7 tests passing in `test_scoring.py`)
- [x] Next.js 16 frontend setup with TypeScript, SSE stream reader, and App Router
- [x] "Nocturnal Voyager" dark glassmorphic design system tokens in `globals.css`

---

## Phase 1: Real Data Pipeline & Spatial Clustering (COMPLETED)
- [x] **Intake Agent** (`intake_agent.py`):
  - [x] Gemini 3.5 Flash / Groq structured JSON slot extraction
  - [x] Regex rule-based fallback parser (zero-key mode)
- [x] **Places Tool** (`places_tool.py`):
  - [x] Nominatim OpenStreetMap city geocoding (free, no key)
  - [x] OpenTripMap flat JSON parser for real attractions
  - [x] Google Places API enrichment (photos, ratings, review counts)
  - [x] ChromaDB destination cache integration (excluding legacy mock stops)
- [x] **Planner Agent** (`planner_agent.py`):
  - [x] Pure-Python k-means spatial clustering (guaranteeing exact k non-empty clusters)
  - [x] Gemini 3.5 Flash day themes & per-stop narrations with `safe_extract_text`
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

## Phase 2: Niche Signal Scraping & Scoring Engine (COMPLETED)
- [x] **Tavily Search Tool** (`backend/app/tools/tavily_tool.py`):
  - [x] Query travel blogs & Reddit discussions using `TAVILY_API_KEY`
  - [x] Extract place snippets, URLs, and source attributions with rich mock fallbacks
- [x] **Reddit Public Scraper Tool** (`backend/app/tools/reddit_tool.py`):
  - [x] Query Reddit public JSON search API with custom `User-Agent` (zero auth/zero key requirement)
  - [x] Extract post titles, selftext snippets, and community upvote metrics
- [x] **Niche Extractor & Sentiment Pipeline** (`backend/app/tools/niche_scraper.py`):
  - [x] LLM structured extraction (Groq/Gemini) + curated authentic candidates
  - [x] VADER sentiment intensity analysis on extracted mention contexts
  - [x] Log-normalized hidden gem score calculation via `compute_hidden_gem_score`
  - [x] ChromaDB caching in `niche_spots` collection
- [x] **Ranker Agent** (`backend/app/agents/ranker_agent.py`):
  - [x] Wire ranker node into LangGraph: `intake -> ranker -> planner -> END`
  - [x] Blends mainstream OpenTripMap attractions with niche-scored spots by `niche_weight`
  - [x] Pace-aware stop selection and category diversity
- [x] **Test Suite Verification**:
  - [x] 11/11 tests passing in pytest (`test_scoring.py` + `test_phase2_ranker.py`)

---

## Phase 3: Conversational Intake, Regional Spatial Dispersion & UI Overhaul (COMPLETED)
- [x] **Conversational Intake with Clarifying Questions** (`intake_agent.py`):
  - [x] Detect underspecified prompts (e.g. *"3 day trip in Goa"*)
  - [x] Generate 2–3 contextual clarifying questions with interactive quick-reply chips
  - [x] Provide 1-click **"Plan with defaults now"** bypass option
  - [x] Destination persistence across clarification turns
- [x] **Regional Multi-Zone Discovery & Spatial Dispersion** (`places_tool.py`):
  - [x] State/region awareness for wide destinations (Goa, Rajasthan, Bali, Kerala, Mumbai, Pune, Delhi, Jaipur)
  - [x] Multi-centroid / adaptive radius discovery to eliminate 6km micro-clustering
  - [x] K-means assigns geographically distinct sub-regions per day
- [x] **Routing & Weather Tools**:
  - [x] `routing_tool.py`: Calculate realistic walking & transit minutes between consecutive stops
  - [x] `weather_tool.py`: Open-Meteo daily weather forecast attached to `DayPlan.weather_note`
- [x] **Smart Currency Formatter** (`currency.ts`):
  - [x] Indian trips formatted in `₹ INR` (e.g. ₹1,200 / ₹4,500), international in `$ USD`
- [x] **Centered Studio UI & Wide Side-by-Side Map/Timeline Layout** (`page.tsx`, `ChatPanel.tsx`, `ItineraryView.tsx`, `MapView.tsx`, `globals.css`):
  - [x] Large prominent centered conversational studio hub
  - [x] Expansive side-by-side Map + Day-by-Day Timeline workspace below chat
  - [x] Safe day tab indexing and error-proof Leaflet bounds handling

---

## Phase 4: Multi-Turn Conversational Editing & State Iteration (NEXT)
- [ ] Multi-turn intent classifier (new trip vs edit stop vs adjust pace vs change budget)
- [ ] LangGraph state checkpoint time-travel recovery
- [ ] UI follow-up quick action prompts ("swap stop 2", "make day 1 more relaxed")

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
