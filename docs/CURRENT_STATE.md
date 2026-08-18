# Current Project State
> Last updated: 2026-08-18

---

## Project Overview

**WanderAI** is a versatile multi-agent AI travel planner designed to plan complete, personalized day-by-day itineraries across any global or regional destination — seamlessly balancing iconic must-see sights, authentic hidden gems, budget constraints, and spatial pacing.

---

## What's Completed

### Phase 0 — Foundations (100%)
- FastAPI backend with `/plan` (REST), `/plan/stream` (SSE), `/health`, `/export/pdf` stub
- LangGraph `StateGraph` with SQLite checkpointer (`data/checkpoints.db`) and JsonPlusSerializer
- All Pydantic schemas: `TripRequest -> Stop -> DayPlan -> Itinerary -> AgentEvent`
- Embedded Chroma vector store (`niche_spots` + `itinerary_cache`)
- Log-normalised hidden gem scoring formula (7/7 unit tests passing)
- Next.js 16 frontend with "Nocturnal Voyager" dark design system
- Multi-section scrollable landing page & HTML5 Canvas Live Wallpaper (Delhi, Mumbai, Jaipur, Goa, Bengaluru)
- Leaflet + CartoDB Dark Matter map integration (zero token / no credit card requirement)

### Phase 1 — Real Data Pipeline & Spatial Clustering (100%)
- Intake Agent (Groq Llama 3.1 8B slot extraction + regex fallback)
- Places Tool (Nominatim geocoding + OpenTripMap attractions + Google Places enrichment + Chroma caching)
- Planner Agent (Pure-Python k-means coordinate clustering + Gemini 2.5 Flash day themes & narrations)

### Phase 2 — Niche Signal Scraping & Scoring Engine (100%)
- Tavily travel search tool (`tavily_tool.py`) with blog & Reddit snippet extraction
- Reddit public discussion scraper (`reddit_tool.py`) with zero auth / zero key requirement
- Niche scraper & scoring pipeline (`niche_scraper.py`) with VADER sentiment intensity analysis
- Ranker Agent (`ranker_agent.py`) blending mainstream attractions and authentic hidden gems by `niche_weight`
- 11/11 tests passing in pytest suite

---

## Active Phase (Phase 3)

1. **Conversational Intake with Clarifying Questions**:
   - Detects brief prompts (e.g. *"3 day trip in Goa"*) and asks 2–3 targeted questions with interactive chips in chat.
   - Includes 1-click **"Plan with defaults now"** bypass button.
2. **Regional Multi-Zone Spatial Dispersion**:
   - Fixes the 6km micro-clustering issue for states/regions (Goa, Rajasthan, Bali) by querying diverse sub-regions and assigning distinct zones per day.
3. **Routing & Weather Tools**:
   - OpenRouteService / Haversine transit minutes between consecutive stops.
   - Open-Meteo daily weather summaries attached to each day.
4. **Centered Studio Layout**:
   - Prominent centered conversational hub unfolding into an expansive side-by-side Map + Timeline visualizer.
