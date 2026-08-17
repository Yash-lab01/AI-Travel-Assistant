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
| **LLMs (Zero Cost Strategy)** | • **Groq `llama-3.1-8b-instant`**: Fast structured slot-filling (Intake Agent)<br>• **Gemini 2.5 Flash (`GOOGLE_AI_STUDIO_API_KEY`)**: Day themes, storytelling & narrations<br>• **Local LoRA (Ollama `Llama 3.2 3B`)**: Atmospheric stop narration |
| **Place & Travel Data** | • **Nominatim (OpenStreetMap)**: Free city geocoding<br>• **OpenTripMap API**: Attractions & POI categories<br>• **Google Places API**: Photo & rating enrichment<br>• **Tavily API**: Niche travel search & blog extraction |
| **Vector Store** | ChromaDB (Embedded on-disk — `niche_spots` & `itinerary_cache`, no Docker) |
| **Scoring Engine** | Custom log-normalized hidden gem formula (unit tested with 7/7 tests passing) |
| **Frontend Framework** | Next.js 16 (App Router), React 19, TypeScript, Vanilla CSS |
| **Interactive Map** | Leaflet + CartoDB Dark Matter tiles (100% free, zero token / no credit card requirement) + custom glowing markers |
| **Live Wallpaper** | HTML5 Canvas 2D engine with global & Indian flight paths and aurora atmosphere |
| **Design System** | "Nocturnal Voyager" (Playfair Display headlines, Outfit body, Sora labels, glassmorphism) |

---

## 3. Key Architecture Decisions

1. **Async-Only LangGraph Execution**:
   - All agent nodes are defined as `async def node(state: TravelGraphState) -> dict`.
   - The graph must ALWAYS be invoked using `await travel_graph.ainvoke(...)` or `travel_graph.astream(...)`. Sync `.invoke()` causes a `TypeError`.
2. **Deterministic Multi-Agent State Machine**:
   - `intake_node` extracts structured slots (`TripRequest`) with fallback regex when no key is set.
   - `places_tool` fetches POIs and caches results in Chroma by destination hash.
   - `planner_node` executes pure-Python k-means coordinate clustering (k = num_days) to ensure spatial coherence (no cross-city zig-zagging).
   - `ranker_node` (Phase 2) balances popular POIs and niche-scored spots according to `niche_weight`.
3. **Embedded Chroma (No Docker)**:
   - Persisted locally in `backend/chroma_data/` to keep local development zero-friction.
4. **Pydantic Schema as Single Source of Truth**:
   - `backend/app/models/schemas.py` defines `TripRequest`, `Stop`, `DayPlan`, `Itinerary`, `NicheScore`, and `AgentEvent`.
   - `frontend/src/types/index.ts` strictly mirrors these models 1:1.
   - `DayPlan.date` is stored as `Optional[str]` (ISO string) to avoid SQLite msgpack serialization issues.
5. **Zero-Key Resilient Fallback Design**:
   - Every component works gracefully even if API keys are missing (falls back to regex intake, heuristic clustering, CartoDB maps, and mock places).
6. **Zero-Token Dark Map**:
   - Map uses Leaflet + CartoDB Dark Matter tiles to avoid Mapbox billing/credit-card blockers.

---

## 4. Core Directory Layout & Entry Points

```
AI Travel Assistant/
├── .context/                       # Persistent memory system for LLM continuity
│   ├── PROJECT_CONTEXT.md          # Architecture & conventions
│   ├── TASKS.md                    # Detailed roadmap & milestone checklist
│   └── HANDOFF.md                  # Session progress & immediate next steps
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point (SSE & REST endpoints)
│   │   ├── agents/
│   │   │   ├── intake_agent.py     # Groq LLM + regex slot-filling
│   │   │   ├── planner_agent.py    # K-means clustering + Gemini themes
│   │   │   └── ranker_agent.py     # (Phase 2) Popular + Niche blending
│   │   ├── tools/
│   │   │   ├── places_tool.py      # Nominatim + OpenTripMap + Google Places
│   │   │   ├── reddit_tool.py      # (Phase 2) Reddit JSON scraper
│   │   │   └── tavily_tool.py      # (Phase 2) Tavily blog search
│   │   ├── graph/
│   │   │   ├── state.py            # TravelGraphState TypedDict
│   │   │   └── travel_graph.py     # LangGraph compilation & routing
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic data contracts
│   │   ├── scoring/
│   │   │   └── hidden_gem_score.py # Log-normalized scoring formula
│   │   └── vector_store/
│   │       └── chroma_client.py    # Embedded Chroma client singleton
│   ├── tests/                      # Unit tests (pytest)
│   └── test_phase1.py              # E2E integration test
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Master scrollable landing & studio layout
│   │   │   └── globals.css         # Nocturnal Voyager CSS tokens & animations
│   │   ├── components/
│   │   │   ├── ChatPanel.tsx       # SSE streaming conversation UI
│   │   │   ├── ItineraryView.tsx   # Day tabs, stop cards, summary stats
│   │   │   ├── MapView.tsx         # Leaflet + CartoDB dark map component
│   │   │   ├── AgentEventFeed.tsx  # Real-time agent thought stream
│   │   │   └── TravelLiveWallpaper.tsx # HTML5 Canvas animated flight paths
│   │   └── types/
│   │       └── index.ts            # TypeScript interfaces matching schemas.py
├── stop-servers.ps1                # Script to free ports 3000 & 8000
├── PROJECT_STATUS.md               # Human-readable phase documentation
└── README.md                       # Public repository documentation
```

---

## 5. Coding Conventions

- **Python**: Follow PEP8, type annotations on all function signatures, `async def` for all LangGraph nodes and FastAPI route handlers.
- **Frontend**: Client components with `'use client'`, styling in `globals.css` using CSS custom properties (`--amber`, `--teal`, `--glass-bg`), clean TypeScript types without `any`.
- **Git Commits**: Conventional commits format (`feat(scope): ...`, `fix(scope): ...`, `docs: ...`).
- **Context Updates**: Whenever making changes, update `.context/TASKS.md` and `.context/HANDOFF.md`.
