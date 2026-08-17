# AGENTS.md — AI Travel Assistant

Quick reference for any coding agent working on this repo.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend runtime | Python 3.12+, FastAPI, Uvicorn |
| Agent orchestration | LangGraph `StateGraph` (async) |
| LLM — slot-filling | Groq `llama-3.1-8b-instant` via `langchain-groq` |
| LLM — themes/narrations | Gemini 2.5 Flash via `langchain-google-genai` |
| Place data | OpenTripMap (attractions) + Nominatim (geocoding) + Google Places (enrichment) |
| Vector store | Chroma (embedded, no Docker) |
| Scoring | Custom formula in `backend/app/scoring/hidden_gem_score.py` |
| Frontend | Next.js 16 (App Router), TypeScript, Vanilla CSS |
| Map | Mapbox GL JS v3 (dynamically loaded) |
| Fonts | Playfair Display (headlines), Outfit (body), Sora (labels) |
| Package manager | pip + venv (`backend/.venv`), npm (`frontend/`) |
| VCS | Git, remote on GitHub (`Yash-lab01/AI-Travel-Assistant`) |

---

## Architecture

```
User message
    ¦
    ?
FastAPI /plan/stream (SSE)
    ¦  POST {session_id, message}
    ?
LangGraph ainvoke (ALWAYS async — never use .invoke())
    ¦
    +-? intake_node      — Groq LLM ? TripRequest (regex fallback if no key)
    ¦
    +-? planner_node     — OpenTripMap places ? k-means cluster ? DayPlan[]
              ¦           Gemini assigns themes + narrations (heuristic fallback)
              ?
         Itinerary (Pydantic) streamed as SSE events to frontend
              ¦
              ?
    Next.js frontend
        +- ChatPanel        (SSE client + prompt chips)
        +- AgentEventFeed   (live agent step display)
        +- ItineraryView    (day tabs + stop cards)
        +- MapView          (Mapbox GL JS, lazy-loaded)
```

**Data flow contract:** Every LangGraph node returns a `dict` updating `TravelGraphState`. Nodes are `async def`. The graph is compiled once at import time in `travel_graph.py`.

---

## Project Layout

```
backend/
  app/
    agents/         # intake_agent.py, planner_agent.py  (add new agents here)
    tools/          # places_tool.py                     (add new tools here)
    scoring/        # hidden_gem_score.py                (pure functions, tested)
    vector_store/   # chroma_client.py
    graph/          # travel_graph.py, state.py
    models/         # schemas.py  ? single source of truth for all types
    main.py         # FastAPI app
  tests/            # pytest, run with: .venv\Scripts\pytest
  data/             # checkpoints.db (auto-created, gitignored)

frontend/
  src/
    app/
      globals.css   # ALL design tokens live here — edit here, not inline
      page.tsx      # Root layout only
    components/     # One file per component
    types/          # TypeScript types mirroring backend Pydantic schemas exactly

docs/
  CURRENT_STATE.md  # Phase completion status + next steps (keep updated)
PROJECT_STATUS.md   # High-level roadmap
AGENTS.md           # This file
.env.example        # All env vars with descriptions
```

---

## Coding Conventions

### Backend (Python)
- All LangGraph nodes must be `async def node(state: TravelGraphState) -> dict`
- Call the graph with `await travel_graph.ainvoke(...)` — **never** `.invoke()` or `asyncio.to_thread(invoke)`
- Every node must return only the state keys it changes (partial update)
- Add `AgentEvent` entries to `state["events"]` to stream progress to the frontend
- Use `Optional[X] = None` with graceful fallbacks everywhere — the app must run without any API keys
- New tools go in `backend/app/tools/`, new agents in `backend/app/agents/`
- Schema changes in `schemas.py` require deleting `data/checkpoints.db` (stale serialised state causes Pydantic `model_rebuild()` errors)
- `DayPlan.date` is `Optional[str]` (ISO string) — not `datetime.date` (SQLite checkpointer serialisation issue)
- Run tests before committing: `.venv\Scripts\pytest tests/`

### Frontend (TypeScript / Next.js)
- All CSS tokens and animations are in `globals.css` — do not add inline styles for colours/fonts/spacing
- TypeScript types in `src/types/` must stay in sync with backend Pydantic schemas
- Components are client components (`'use client'`) — avoid server components unless clearly needed
- Lazy-load heavy components (e.g. MapView uses `lazy()` + `Suspense`)
- Use CSS class names from `globals.css` (`.stop-card`, `.day-tab`, `.gem-badge`, etc.), not ad-hoc inline styles

### General
- All new features must have a no-API-key fallback (mock data or heuristic)
- Commit messages follow `type(scope): description` — e.g. `feat(agents)`, `fix(schema)`, `docs`
- Never commit `.env` — only `.env.example`
- Never commit `data/checkpoints.db` or `chroma_data/` (both gitignored)

---

## Important Constraints

1. **Async-only graph** — LangGraph nodes are async. Any sync function called inside must use `await asyncio.get_event_loop().run_in_executor()` if blocking.
2. **No numpy/scipy** — k-means is implemented in pure Python. Keep it that way unless there is a strong reason to add the dependency.
3. **No Docker required** — Chroma runs embedded. Do not introduce services that need Docker for local dev.
4. **Free-tier LLMs only** — Groq (llama-3.1-8b-instant) for latency-sensitive calls, Gemini 2.5 Flash for richer generation. Do not use paid Claude or GPT-4 endpoints.
5. **Schema = source of truth** — `backend/app/models/schemas.py` defines all data shapes. Frontend `types/` mirrors them exactly. If you change one, change the other.
6. **Chroma cache** — `places_tool.py` caches OTM results by destination hash. Do not bypass the cache in new tools; extend it.
7. **SSE event contract** — The frontend expects `event: agent_event` and `event: itinerary` SSE events with specific JSON shapes. Do not rename or restructure these.

---

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | No | Enables Groq LLM in intake agent (regex fallback used if absent) |
| `GOOGLE_API_KEY` | No | Enables Gemini for day themes + narrations |
| `OPENTRIPMAP_API_KEY` | No | Real attraction data (mock used if absent) |
| `GOOGLE_PLACES_API_KEY` | No | Photo/rating enrichment |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | No | Enables interactive map (placeholder shown if absent) |
| `TAVILY_API_KEY` | No | Phase 2 — niche scraping |

---

## Running Locally

```powershell
# Backend
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev
```

Visit http://localhost:3000. Backend API at http://localhost:8000/docs.

---

## Current Phase

**Phase 1 complete.** See `docs/CURRENT_STATE.md` for exact next steps (Phase 2: Reddit/Tavily niche scraping + Ranker Agent).
