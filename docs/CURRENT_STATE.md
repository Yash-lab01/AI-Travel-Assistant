# Current Project State
> Last updated: 2026-08-19

---

## Project Overview

**WanderAI** is a versatile multi-agent AI travel planner designed to plan complete, personalized day-by-day itineraries across any global or regional destination — seamlessly balancing iconic must-see sights, authentic hidden gems, budget constraints, and spatial pacing.

---

## What's Completed

### Phase 0 — Foundations (100%)
- FastAPI backend with `/plan` (REST), `/plan/stream` (SSE), `/health`, `/export/pdf`
- LangGraph `StateGraph` with SQLite checkpointer (`data/checkpoints.db`) and JsonPlusSerializer
- All Pydantic schemas: `TripRequest -> Stop -> DayPlan -> Itinerary -> AgentEvent`
- Embedded Chroma vector store (`niche_spots` + `itineraries`)
- Log-normalised hidden gem scoring formula (7/7 unit tests passing)
- Next.js 16 frontend with "Nocturnal Voyager" dark design system
- Multi-section scrollable landing page & HTML5 Canvas Live Wallpaper
- Leaflet + CartoDB Dark Matter map integration (zero token / free)

### Phase 1 — Real Data Pipeline & Spatial Clustering (100%)
- Intake Agent (Gemini 3.5 Flash / Groq slot extraction + robust regex fallback)
- Places Tool (Nominatim geocoding + OpenTripMap flat JSON parser + Google Places enrichment + Chroma caching)
- Planner Agent (Pure-Python k-means coordinate clustering + Gemini 3.5 Flash day themes & narrations)

### Phase 2 — Niche Signal Scraping & Scoring Engine (100%)
- Tavily travel search tool (`tavily_tool.py`) with blog & Reddit snippet extraction
- Reddit public discussion scraper (`reddit_tool.py`) with zero auth / zero key requirement
- Niche scraper & scoring pipeline (`niche_scraper.py`) with VADER sentiment intensity analysis
- Ranker Agent (`ranker_agent.py`) blending mainstream attractions and authentic hidden gems by `niche_weight`
- 11/11 tests passing in pytest suite

### Phase 3 — Real-World Enhancements & UX Polish (100%)
1. **Conversational Clarifications**: Detects brief prompts and asks 2–3 targeted questions with interactive chips, preserving destination across turns.
2. **Regional Multi-Zone Dispersion**: Queries distinct subzone centroids for states/regions (Goa, Rajasthan, Bali, Mumbai, Pune, Delhi, Kerala) to ensure broad day-by-day spatial distribution.
3. **Transit Times & Weather**: Routing tool calculates sequential travel times; Open-Meteo provides live daily weather forecasts per day.
4. **Smart Currency Formatter**: Displays `₹ INR` for all Indian destinations and `$ USD` for international trips.
5. **Nocturnal Planning Studio UI**: Centered conversational studio unfolding into an interactive side-by-side Timeline + Map visualizer.
6. **Error-Proof Resiliency**: Safe LLM string extraction, guaranteed `k` day clustering, and safe Leaflet marker bounds.

---

## Reference Documents
- [`docs/TROUBLESHOOTING_AND_MISTAKES.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/docs/TROUBLESHOOTING_AND_MISTAKES.md) — Persistent log of known pitfalls, model quirks, and rules for what NOT to do.
- [`.context/PROJECT_CONTEXT.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/.context/PROJECT_CONTEXT.md) — High-level architecture & tech stack.
- [`.context/TASKS.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/.context/TASKS.md) — Granular phase task checklist.
- [`.context/HANDOFF.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/.context/HANDOFF.md) — Current session status & immediate next steps.
