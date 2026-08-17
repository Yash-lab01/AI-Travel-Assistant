# WanderAI — Project Architecture, Status & Roadmap

> **WanderAI** is a versatile multi-agent AI travel planner designed to plan complete, personalized day-by-day itineraries across any global destination — whether travelers want must-see iconic landmarks, authentic local hidden gems, or a balanced blend of both.

---

## High-Level Vision & Core Differentiators

Most AI travel demos are a thin wrapper around a single search prompt. WanderAI is engineered as an autonomous multi-agent state machine that plans, discovers, ranks, and clusters trips across global & regional destinations:

1. **Tool-Orchestrated Multi-Agent Reasoning**: A deterministic LangGraph state machine where specialized agents (Intake slot-filling, Place Discovery, Ranker blending, Spatial Clustering, Thematic Storytelling) query live tools (OpenTripMap, Google Places, Reddit, Tavily, weather, routing) and adapt dynamically.
2. **Versatile Planning with Hidden Gem Engine**: Seamlessly plan classic sightseeing trips, balanced vacations, or deep off-the-beaten-path expeditions. Our log-normalized scoring formula cross-references mainstream popularity signals (Google Places review counts) against niche community sentiment (Reddit, travel blogs) to surface spots that are *actually* under-the-radar.
3. **Spatial Geo-Clustering & Pacing**: Pure-Python k-means coordinate clustering groups attractions into seamless, walking-optimized daily segments without exhausting cross-city zig-zagging.
4. **Applied Fine-Tuning**: A small local model (LoRA-tuned Llama 3B) trained on CC-licensed travel writing, used for evocative stop narration.

---

## Feature Implementation Status

### ✅ Phase 0 — Foundations (100% Completed)
- FastAPI backend (`/plan`, `/plan/stream`, `/health`)
- LangGraph `StateGraph` skeleton with SQLite checkpointer
- All Pydantic data schemas & 1:1 TypeScript interfaces
- Embedded ChromaDB vector store
- Log-normalized hidden gem scoring formula (7/7 unit tests passing)
- Next.js 16 frontend with "Nocturnal Voyager" dark glassmorphism design system

### ✅ Phase 1 — Real Data Pipeline & Spatial Clustering (100% Completed)
- **Intake Agent**: Groq Llama 3.1 8B structured JSON extraction + regex fallback
- **Places Discovery Tool**: Nominatim geocoding + OpenTripMap attraction fetching + Google Places enrichment + Chroma caching
- **Geo-Clustering Planner**: Pure-Python k-means spatial clustering + Gemini 2.5 Flash day themes & narrations
- **Scrollable Landing Page & Interactive Studio**: Sticky glass navbar, hero headline, quick-start prompt cards, stats strip, architecture cards
- **Interactive Live Wallpaper**: HTML5 Canvas with global and Indian flight paths (Delhi, Mumbai, Jaipur, Goa, Bengaluru)
- **Zero-Token Dark Map**: Leaflet + CartoDB Dark Matter tiles (zero card / zero token dependency)

### ✅ Phase 2 — Niche Signal Scraping & Scoring Engine (100% Completed)
- **Tavily Search Tool** (`tavily_tool.py`): Queries travel blogs & Reddit discussions using `TAVILY_API_KEY`
- **Reddit Public Scraper** (`reddit_tool.py`): Zero-auth public JSON scraper with custom `User-Agent`
- **Niche Scraper Pipeline** (`niche_scraper.py`): VADER sentiment analysis on mention contexts, log-normalized scoring, and Chroma caching in `niche_spots`
- **Ranker Agent** (`ranker_agent.py`): Blends mainstream attractions with authentic hidden gems according to `niche_weight` and pace
- **LangGraph Graph**: Wired as `intake -> ranker -> planner -> END`
- **Verification**: 11/11 tests passing in pytest; verified on Lisbon & Rajasthan queries

---

## Upcoming Phases

### Phase 3 — Merged Pipeline + Weather + Routing (NEXT)
- OpenRouteService / Haversine walking & transit time calculations
- Open-Meteo per-day weather forecasting attached to `DayPlan.weather_note`
- Progressive SSE streaming (`day_ready` event emission)

### Phase 4 — Fine-Tuning (Local Narration Model)
- Curate CC-licensed travel dataset (Wikivoyage, Project Gutenberg)
- Unsloth + PEFT LoRA training on Llama 3.2 3B (Colab T4)
- Deploy local Ollama model for atmospheric narrations

### Phase 5 — Conversational Editing
- Multi-turn state editing ("swap stop 3", "make day 2 more relaxed")
- Time-travel state recovery

### Phase 6 — Export & Polish
- Playwright headless PDF export
- Shareable itinerary URL slug
