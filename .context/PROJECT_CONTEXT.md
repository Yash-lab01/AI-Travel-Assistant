# PROJECT_CONTEXT.md — WanderAI

## 1. High-Level Project Goal
**WanderAI** is a versatile multi-agent AI travel planning application designed to create complete, personalized day-by-day itineraries across any global or regional destination. It seamlessly balances **iconic mainstream landmarks** with **authentic local hidden gems**, managing budget constraints, pacing, and spatial coherence with live multi-agent reasoning.

---

## 2. Tech Stack

| Layer | Technologies Used |
|---|---|
| **Backend Runtime** | Python 3.12+, FastAPI, Uvicorn (async) |
| **Agent Orchestration** | LangGraph `StateGraph` (async execution with `ainvoke`/`astream`) |
| **Checkpointer** | SQLite Checkpointer (`backend/data/checkpoints.db`) |
| **LLMs (Active — Zero Cost Strategy)** | • **Google Gemini (`GOOGLE_API_KEY`)**: `gemini-3.6-flash` (primary, fast reasoning & structured output), `gemini-3.5-flash` (secondary fallback)<br>• **Groq API (`GROQ_API_KEY`)**: `openai/gpt-oss-20b` (primary high-speed slot extraction, dynamic clarifications, planner narration fallback), `openai/gpt-oss-120b` (secondary fallback)<br>• **Local LoRA (Ollama `Llama 3.2 3B`)**: Atmospheric stop narration (Phase 5) |
| **⚠️ Deprecated Models (DO NOT USE)** | `gemini-2.5-flash` (returns 404), `gemini-2.0-flash` (returns 404), `llama-3.1-8b-instant` (returns 404 on Groq), `llama-3.3-70b-versatile` (returns 404 on Groq), `qwen/qwen3.6-27b` (returns 404 on Groq) |
| **Place & Travel Data** | • **Nominatim (OpenStreetMap)**: Free city geocoding<br>• **OpenTripMap API** (`format=json` → flat dicts, NOT GeoJSON): Attractions & POI categories<br>• **Wikipedia REST & Wikimedia Commons APIs**: High-resolution CC landmark lead photography (zero auth)<br>• **Curated Photography & Fallbacks**: 40+ destination landscape banners & category fallbacks<br>• **Tavily API**: Niche travel search & blog extraction |
| **Vector Store** | ChromaDB (Embedded on-disk at `backend/data/chroma_db/` — `niche_spots` & `itineraries`, no Docker) |
| **Scoring Engine** | Custom log-normalized hidden gem formula (unit tested with 7/7 tests passing) |
| **Frontend Framework** | Next.js 16 (App Router), React 19, TypeScript, Vanilla CSS |
| **Interactive Map** | Leaflet + CartoDB Dark Matter tiles (100% free, zero token / no credit card requirement), preloaded `leaflet.css`, glowing polylines, container reuse cleanup |
| **Live Wallpaper** | HTML5 Canvas 2D engine with global & Indian flight paths and aurora atmosphere |
| **Design System** | "Nocturnal Voyager" (Playfair Display headlines, Outfit body, Sora labels, JetBrains Mono numbers, glassmorphism, 12px radii) |

---

## 3. Key Architecture Decisions

1. **Async-Only LangGraph Execution**:
   - All agent nodes are defined as `async def node(state: TravelGraphState) -> dict`.
   - The graph must ALWAYS be invoked using `await travel_graph.ainvoke(...)` or `travel_graph.astream(...)`. Sync `.invoke()` causes a `TypeError`.
2. **Deterministic Multi-Agent State Machine**:
   - `intake_node` extracts structured slots (`TripRequest`) with fallback regex when no key is set.
   - `ranker_node` (Phase 2+3): fetches OTM popular stops AND niche-scraped gems concurrently. **Always outputs a non-empty `ranked_stops`** list.
   - `planner_node` uses ONLY `ranked_stops` from ranker. Never fetches its own OTM data unless ranker completely failed.
   - `planner_node` uses K-means++ for balanced, geographically spread clusters (k = num_days).
3. **Embedded Chroma (No Docker)**:
   - Persisted locally at `backend/data/chroma_db/`.
   - Chroma cache uses `CACHE_VERSION` string (`"v9"`) as part of the key — increment this constant in `places_tool.py` whenever the data schema or parser changes to auto-invalidate stale entries.
   - Only genuine attractions (`source="opentripmap"`) are cached. Fallback mock stops (`source="mock"`) are never written to Chroma.
4. **Pydantic Schema as Single Source of Truth**:
   - `backend/app/models/schemas.py` defines `TripRequest`, `Stop`, `DayPlan`, `Itinerary`, `NicheScore`, and `AgentEvent`.
   - `frontend/src/types/index.ts` strictly mirrors these models 1:1.
   - `DayPlan.date` is stored as `Optional[str]` (ISO string) to avoid SQLite msgpack serialization issues.
5. **Safe LLM Response Extraction**:
   - `response.content` from `langchain_google_genai` may be a `list[dict]` (not `str`).
   - Always use the `safe_extract_text(content: Any) -> str` function defined in each agent. **Never call `response.content.strip()` directly.**
6. **Zero-Key Resilient Fallback Design**:
   - Every component works gracefully even if API keys are missing (falls back to regex intake, heuristic clustering, CartoDB maps, and mock places).
   - Mock places are ONLY used when `OTM_KEY` is entirely absent. If key exists but OTM returns 0, retry with wider radius first.
7. **Zero-Token Dark Map**:
   - Map uses Leaflet + CartoDB Dark Matter tiles to avoid Mapbox billing/credit-card blockers.
8. **Smart Currency Formatting**:
   - `frontend/src/utils/currency.ts` detects Indian destinations and formats costs in ₹ INR; international trips use $ USD.

---

## 4. Core Directory Layout & Entry Points

```
AI Travel Assistant/
├── .context/                       # Persistent memory system for LLM continuity
│   ├── PROJECT_CONTEXT.md          # Architecture & conventions (THIS FILE)
│   ├── TASKS.md                    # Detailed roadmap & milestone checklist
│   └── HANDOFF.md                  # Session progress & immediate next steps
├── docs/
│   ├── CURRENT_STATE.md            # Human-readable phase completion status
│   └── TROUBLESHOOTING_AND_MISTAKES.md  # Bug log, root causes, what NOT to do
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point (SSE & REST endpoints)
│   │   ├── agents/
│   │   │   ├── intake_agent.py     # Gemini 3.6 Flash / Groq gpt-oss-20b slot-filling + dynamic clarifications
│   │   │   ├── planner_agent.py    # K-means++ clustering + Gemini 3.6 themes & narrations (Groq gpt-oss-20b fallback)
│   │   │   ├── ranker_agent.py     # Popular + Niche blending (always non-empty output)
│   │   │   └── editor_agent.py     # Multi-turn conversational itinerary editing & state patching
│   │   ├── tools/
│   │   │   ├── places_tool.py      # Nominatim + OpenTripMap + Wikipedia/Wikimedia cascade + v8 Chroma cache
│   │   │   ├── destination_images.py # Curated 40+ destination banners + category photography
│   │   │   ├── niche_scraper.py    # Reddit/Tavily scraper + VADER sentiment + hidden gem scoring
│   │   │   ├── routing_tool.py     # Haversine transit time calculation between stops
│   │   │   ├── weather_tool.py     # Open-Meteo daily weather forecast per day
│   │   │   ├── reddit_tool.py      # Reddit public JSON scraper (zero auth)
│   │   │   ├── tavily_tool.py      # Tavily blog search tool
│   │   │   ├── pdf_generator.py    # Headless Playwright A4 PDF export
│   │   │   ├── ical_generator.py   # RFC 5545 iCalendar (.ics) export
│   │   │   ├── packing_list_generator.py # Weather-aware packing checklist
│   │   │   └── ollama_narrator.py  # Local LoRA Llama 3.2 3B narrator client
│   │   ├── graph/
│   │   │   ├── state.py            # TravelGraphState TypedDict
│   │   │   └── travel_graph.py     # LangGraph compilation & routing
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic data contracts
│   │   ├── scoring/
│   │   │   └── hidden_gem_score.py # Log-normalized scoring formula
│   │   ├── db/
│   │   │   ├── history_store.py    # SQLite trip history store
│   │   │   └── feedback_store.py   # SQLite user thumbs feedback store
│   │   └── vector_store/
│   │       └── chroma_client.py    # Embedded Chroma client singleton (path: data/chroma_db/)
│   ├── data/
│   │   ├── checkpoints.db          # SQLite LangGraph checkpoints
│   │   ├── trip_history.db         # SQLite saved itineraries
│   │   ├── user_feedback.db        # SQLite stop thumbs ratings
│   │   └── chroma_db/              # ChromaDB on-disk store (collections: niche_spots, itineraries)
│   └── tests/                      # Unit tests (pytest) — 36/36 passing
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Master scrollable landing & studio layout
│   │   │   ├── trip/[slug]/page.tsx # Public read-only shareable trip route
│   │   │   ├── layout.tsx          # Root layout with preloaded Leaflet CSS & Google Fonts
│   │   │   └── globals.css         # Nocturnal Voyager CSS tokens & animations
│   │   ├── components/
│   │   │   ├── ChatPanel.tsx       # SSE streaming conversation UI + clarification chips
│   │   │   ├── ItineraryView.tsx   # Day tabs, full-bleed stop cards, 3D tilt, timeline switcher
│   │   │   ├── MapView.tsx         # Leaflet + CartoDB dark map (safe lat/lon, route lines, bounds validation)
│   │   │   ├── AgentEventFeed.tsx  # Real-time agent thought stream
│   │   │   ├── TravelLiveWallpaper.tsx  # HTML5 Canvas animated flight paths + aurora atmosphere
│   │   │   ├── TripHistoryPanel.tsx # Saved trips slide-over drawer
│   │   │   ├── ShareModal.tsx      # Public share & export dialog
│   │   │   ├── PackingListModal.tsx # Weather-aware packing checklist modal
│   │   │   ├── ErrorBoundary.tsx   # React error boundary
│   │   │   └── Toast.tsx           # Floating toast notification manager
│   │   ├── utils/
│   │   │   ├── currency.ts         # Smart ₹ INR / $ USD formatter by destination
│   │   │   ├── timeline.ts         # Sequential 09:00 AM time-slot calculator
│   │   │   └── destinationTheme.ts # 5-archetype dynamic CSS palette engine
│   │   └── types/
│   │       └── index.ts            # TypeScript interfaces matching schemas.py
├── stop-servers.ps1                # Script to free ports 3000 & 8000
└── README.md                       # Public repository documentation
```

---

## 5. Coding Conventions

- **Python**: PEP8, type annotations on all function signatures, `async def` for all LangGraph nodes and FastAPI route handlers.
- **LLM Response Safety**: Always use `safe_extract_text(response.content)` — never `response.content.strip()` directly.
- **Chroma Cache**: Increment `CACHE_VERSION` in `places_tool.py` whenever OTM parser, image pipeline, or Stop schema changes (currently `v9`).
- **Frontend**: Client components with `'use client'`, styling in `globals.css` using CSS custom properties (`--amber`, `--teal`, `--glass-bg`), clean TypeScript types.
- **Git Commits**: Conventional commits format (`feat(scope): ...`, `fix(scope): ...`, `docs: ...`). **Always make separate, atomic commits** for `docs`, `frontend`, and `backend` (never bundle them all into a single monolithic commit) so commit messages are direct and easy to track.
- **Context Updates**: Whenever making changes, update `.context/TASKS.md`, `.context/HANDOFF.md`, and `docs/TROUBLESHOOTING_AND_MISTAKES.md` if a new bug/pattern was encountered.
- **Clarification Question Chain**: `intake_node` uses a 3-tier chain: (1) Static `DESTINATION_QUESTIONS` dict for known cities (Goa, Mumbai, Lisbon…) — fastest, no LLM call; (2) `_generate_dynamic_clarification_questions()` for unknown destinations — Gemini 3.6 Flash → Groq `openai/gpt-oss-20b` fallback generates contextual questions from the *actual* user prompt; (3) `_get_generic_clarification_questions()` as last resort if all LLMs fail.
