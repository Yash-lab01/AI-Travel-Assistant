# Current Project State
> Last updated: 2026-08-17

---

## What's Completed

### Phase 0 — Foundations (100%)
- FastAPI backend with `/plan` (REST), `/plan/stream` (SSE), `/health`, `/export/pdf` stub
- LangGraph `StateGraph` with SQLite checkpointer (`data/checkpoints.db`)
- All Pydantic schemas: `TripRequest ? Stop ? DayPlan ? Itinerary ? AgentEvent`
- Embedded Chroma vector store (no Docker) — `niche_spots` + `itinerary_cache` collections
- Hidden gem scoring formula (`compute_hidden_gem_score`) — log-normalised, 7/7 unit tests passing
- Next.js 16 frontend with SSE streaming client
- "Nocturnal Voyager" design system (deep navy, amber/teal, glassmorphism, Playfair Display + Outfit)
- Animated background (world map dots, radial glow, `bgPulse` keyframe)
- `PROJECT_STATUS.md` at project root with phase-by-phase roadmap

### Phase 1 — Real Data Pipeline (100%)
- **Intake Agent** (`backend/app/agents/intake_agent.py`):
  - Primary: Groq Llama 3.1 8B via `langchain-groq` (structured JSON extraction)
  - Fallback: Rule-based regex parser (no API key required)
  - Extracts: destination, num_days, budget, niche_weight, travel_style, pace, group_type, interests
- **Places Tool** (`backend/app/tools/places_tool.py`):
  - Nominatim (free) for geocoding city ? lat/lon
  - OpenTripMap for attraction fetch (mocked when no key)
  - Google Places enrichment for photos/ratings (optional, graceful fallback)
  - Results cached in Chroma by destination hash
- **Planner Agent** (`backend/app/agents/planner_agent.py`):
  - K-means geo-clustering (pure Python, no numpy) ? geographically coherent days
  - Gemini 2.5 Flash for evocative day themes + per-stop narrations
  - Heuristic fallbacks when no API key
  - Pace-aware stop limits (slow=3, moderate=5, fast=7 stops/day)
- **MapView** (`frontend/src/components/MapView.tsx`):
  - Mapbox GL JS, `navigation-night-v1` dark style
  - Amber markers for popular stops, teal for hidden gems with glow effect
  - Numbered markers, popup cards matching design system
  - Graceful no-token fallback with setup instructions
- **Graph wired** correctly with `ainvoke`/`astream` (async nodes require async API)
- **Tested**: `POST /plan` returns 200, real Lisbon coords, day themes, cost estimates, travel connectors

### Git — All Committed & Pushed
Latest commits on `main`:
1. `feat(phase1)` — Intake Agent, Planner, Places Tool, schema fixes, async graph
2. `feat(design)` — Nocturnal Voyager CSS overhaul
3. `docs` — PROJECT_STATUS.md, finetuning stub

---

## Currently Working On

Nothing in progress. Phase 1 just completed and verified.

---

## Known Issues / Blockers

| Issue | Impact | Status |
|---|---|---|
| No API keys set in `.env` — narrations are generic ("A museum in Lisbon.") | Low — fallbacks work | Needs user to add keys |
| Mapbox map shows "Add token" placeholder | Medium — panel visible but empty | Needs `NEXT_PUBLIC_MAPBOX_TOKEN` in `.env` |
| `budget_usd` not parsed from regex fallback when written as "800 dollars" | Low | Minor regex fix needed |
| LangGraph checkpoint STRICT_MSGPACK warnings about Pydantic enums | Low — non-breaking | Acceptable for now |
| Chroma `itinerary_cache` never invalidated | Low | Phase 3 concern |

---

## Important Decisions Made

| Decision | Rationale |
|---|---|
| **Groq Llama 3.1 8B** for intake (not Claude/GPT-4) | Free tier, generous limits, fast for slot-filling |
| **Gemini 2.5 Flash** for themes/narrations | Free via `GOOGLE_API_KEY`, already a dependency |
| **K-means in pure Python** (no numpy/sklearn) | Avoids heavy ML dep; city-scale clustering is fine |
| **Nominatim** for geocoding | Free, no key, sufficient accuracy |
| **Mock fallback everywhere** | App runs fully without any API keys |
| **`ainvoke` not `invoke` in LangGraph** | All nodes are `async`; sync `invoke` raises `TypeError` |
| **`DayPlan.date` as `Optional[str]`** | Pydantic `Optional[date]` caused serialisation issues with SQLite checkpointer |
| **Delete `checkpoints.db` on schema changes** | Stale serialised Pydantic models in SQLite cause `model_rebuild()` errors |

---

## Relevant Files

```
backend/
  app/
    agents/
      intake_agent.py       # Groq LLM + regex fallback slot extraction
      planner_agent.py      # k-means clustering + Gemini themes/narrations
    tools/
      places_tool.py        # Nominatim + OpenTripMap + Google Places + Chroma cache
    graph/
      travel_graph.py       # LangGraph StateGraph (intake -> planner -> END)
      state.py              # TravelGraphState TypedDict
    models/
      schemas.py            # All Pydantic models
    scoring/
      hidden_gem_score.py   # Scoring formula (tested)
    vector_store/
      chroma_client.py      # Embedded Chroma setup
    main.py                 # FastAPI routes — uses ainvoke/astream
  tests/
    test_scoring.py         # 7/7 passing
  test_phase1.py            # Manual E2E integration test

frontend/
  src/
    app/
      globals.css           # Nocturnal Voyager design system tokens + animations
      page.tsx              # Root layout, animated background, dual-panel grid
    components/
      ChatPanel.tsx         # SSE streaming, prompt chips, message input
      AgentEventFeed.tsx    # Real-time agent event display
      ItineraryView.tsx     # Day tabs, stop cards, map integration, summary bar
      MapView.tsx           # Mapbox GL JS dark map with amber/teal markers

docs/
  CURRENT_STATE.md          # This file
PROJECT_STATUS.md           # High-level phase roadmap (at root)
.env.example                # All required env vars documented
```

---

## Exact Next Steps (Phase 2)

**Goal:** Populate `is_niche=True` with real scoring, sourced from Reddit + Tavily.

1. **Reddit scraper** (`backend/app/tools/reddit_tool.py`)
   - Use `httpx` against Reddit JSON API (no auth needed for public posts)
   - Queries: `"<destination> hidden gems"`, `"<destination> underrated"`, `"<destination> locals"`
   - Extract mentioned place names + surrounding context for sentiment

2. **Tavily blog scraper** (`backend/app/tools/tavily_tool.py`)
   - Tavily Search API (free tier: 1000 queries/month)
   - Queries: `"best hidden gems in <destination> 2024"`, `"off the beaten path <destination>"`
   - Extract named places + snippet context

3. **VADER sentiment** on mention contexts ? `avg_sentiment` field

4. **Wire into scoring** — call `compute_hidden_gem_score()` per stop, set `is_niche=True` if score > 0.55

5. **Ranker Agent** (`backend/app/agents/ranker_agent.py`)
   - Blend OpenTripMap popular stops + niche-scored stops by `niche_weight`
   - Insert into graph: `intake -> planner -> ranker -> END`

6. **Add `TAVILY_API_KEY`** and optionally `REDDIT_CLIENT_ID` to `.env.example`

**Acceptance test:** Lisbon query returns >=2 stops with `is_niche=True`, score > 0.5,
source attribution shown in UI gem badge tooltip.
