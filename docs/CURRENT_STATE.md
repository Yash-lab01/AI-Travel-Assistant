# Current Project State
> Last updated: 2026-08-17

---

## Project Overview

**WanderAI** is a versatile multi-agent AI travel planner designed to plan complete, personalized day-by-day itineraries across any global or regional destination — seamlessly balancing iconic must-see sights, authentic hidden gems, budget constraints, and spatial pacing.

---

## What's Completed

### Phase 0 — Foundations (100%)
- FastAPI backend with `/plan` (REST), `/plan/stream` (SSE), `/health`, `/export/pdf` stub
- LangGraph `StateGraph` with SQLite checkpointer (`data/checkpoints.db`)
- All Pydantic schemas: `TripRequest -> Stop -> DayPlan -> Itinerary -> AgentEvent`
- Embedded Chroma vector store (no Docker) — `niche_spots` + `itinerary_cache` collections
- Hidden gem scoring formula (`compute_hidden_gem_score`) — log-normalised, 7/7 unit tests passing
- Next.js 16 frontend with SSE streaming client
- "Nocturnal Voyager" design system (deep navy, amber/teal, glassmorphism, Playfair Display + Outfit)
- Multi-section scrollable landing page + interactive planning studio (`#planner-studio`)
- Interactive travel-themed Live Wallpaper (`TravelLiveWallpaper.tsx`) with global & Indian flight arcs (Delhi, Mumbai, Jaipur, Goa, Bengaluru) and pulsing beacon nodes

### Phase 1 — Real Data Pipeline (100%)
- **Intake Agent** (`backend/app/agents/intake_agent.py`):
  - Primary: Groq Llama 3.1 8B via `langchain-groq` (structured JSON extraction)
  - Fallback: Rule-based regex parser (no API key required)
  - Extracts: destination, num_days, budget, niche_weight, travel_style, pace, group_type, interests
- **Places Tool** (`backend/app/tools/places_tool.py`):
  - Nominatim (free) for geocoding city -> lat/lon
  - OpenTripMap for attraction fetch (mocked when no key)
  - Google Places enrichment for photos/ratings (optional, graceful fallback)
  - Results cached in Chroma by destination hash
- **Planner Agent** (`backend/app/agents/planner_agent.py`):
  - K-means geo-clustering (pure Python, no numpy) -> geographically coherent days
  - Gemini 2.5 Flash for evocative day themes + per-stop narrations
  - Heuristic fallbacks when no API key
  - Pace-aware stop limits (slow=3, moderate=5, fast=7 stops/day)
- **MapView** (`frontend/src/components/MapView.tsx`):
  - Mapbox GL JS, `navigation-night-v1` dark style
  - Amber markers for popular stops, teal for hidden gems with glow effect
  - Numbered markers, popup cards matching design system
- **Graph wired** correctly with `ainvoke`/`astream` (async nodes require async API)
- **Tested**: `POST /plan` returns 200, real coordinates, day themes, cost estimates, travel connectors

---

## Known Issues / Blockers

| Issue | Impact | Status |
|---|---|---|
| No API keys set in `.env` — narrations use fallback descriptions | Low — fallbacks work | Needs user to add keys |
| Mapbox map shows "Add token" placeholder | Medium — panel visible but empty | Needs `NEXT_PUBLIC_MAPBOX_TOKEN` in `.env` |
| LangGraph checkpoint STRICT_MSGPACK warnings about Pydantic enums | Low — non-breaking | Acceptable |
| Chroma `itinerary_cache` never invalidated | Low | Phase 3 concern |

---

## Important Decisions Made

| Decision | Rationale |
|---|---|
| **Versatile Positioning** | Supports both iconic landmark travel planning and niche hidden gem discovery |
| **Indian Travel Elements** | Added Indian hubs (Delhi, Mumbai, Jaipur, Goa, Bengaluru) and curated journeys (Rajasthan, Goa) |
| **Groq Llama 3.1 8B** for intake | Free tier, generous limits, fast for slot-filling |
| **Gemini 2.5 Flash** for themes/narrations | Free via `GOOGLE_API_KEY`, rich language generation |
| **K-means in pure Python** (no numpy/sklearn) | Avoids heavy ML dep; city-scale clustering is fast & lightweight |
| **Nominatim** for geocoding | Free, no key, global coverage |
| **Mock fallback everywhere** | App runs fully without any API keys |
| **`ainvoke` not `invoke` in LangGraph** | All nodes are `async`; sync `invoke` raises `TypeError` |
| **`DayPlan.date` as `Optional[str]`** | Avoids SQLite checkpointer serialisation issues |

---

## Exact Next Steps (Phase 2)

**Goal:** Populate `is_niche=True` with real scoring, sourced from Reddit + Tavily, blending popular & niche stops via the Ranker Agent.

1. **Reddit scraper** (`backend/app/tools/reddit_tool.py`): Extract place mentions & context from public Reddit JSON API.
2. **Tavily blog scraper** (`backend/app/tools/tavily_tool.py`): Travel blog discovery fallback.
3. **VADER sentiment**: Sentiment calculation on mention contexts.
4. **Wire into scoring**: `compute_hidden_gem_score()` per stop.
5. **Ranker Agent** (`backend/app/agents/ranker_agent.py`): Blends popular OpenTripMap attractions + niche stops according to user's `niche_weight` preference (0.0 = popular, 0.5 = balanced, 1.0 = deep niche).
