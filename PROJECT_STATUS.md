# WanderAI — Project Architecture, Status & Roadmap

> **WanderAI** is a versatile multi-agent AI travel planner designed to plan complete, personalized day-by-day itineraries across any global destination — whether travelers want must-see iconic landmarks, authentic local hidden gems, or a balanced blend of both.

---

## High-Level Vision & Core Differentiators

Most AI travel demos are a thin wrapper around a single search prompt. WanderAI is engineered as an autonomous multi-agent state machine that plans, discovers, ranks, and clusters trips across global & regional destinations:

1. **Tool-Orchestrated Multi-Agent Reasoning**: A deterministic LangGraph state machine where specialized agents (Intake slot-filling, Place Discovery, Spatial Clustering, Thematic Storytelling) query live tools (OpenTripMap, Google Places, Reddit, weather, routing) and adapt dynamically.
2. **Versatile Planning with Hidden Gem Engine**: Seamlessly plan classic sightseeing trips, balanced vacations, or deep off-the-beaten-path expeditions. Our log-normalized scoring formula cross-references mainstream popularity signals (Google Places review counts) against niche community sentiment (Reddit, travel blogs) to surface spots that are *actually* under-the-radar, not just under-reviewed.
3. **Spatial Geo-Clustering & Pacing**: Pure-Python k-means coordinate clustering groups attractions into seamless, walking-optimized daily segments without exhausting cross-city zig-zagging.
4. **Applied Fine-Tuning**: A small local model (LoRA-tuned Llama 3B) trained on CC-licensed travel writing, used for evocative stop narration.

---

## Feature Implementation Status

### ✅ Fully Implemented
| Feature | Implementation |
|---|---|
| **Multi-Agent Orchestration** | LangGraph async `StateGraph` with SQLite checkpoint persistence |
| **Intake Agent** | Groq Llama 3.1 8B structured JSON extraction + regex fallback |
| **Places Discovery Tool** | Nominatim geocoding + OpenTripMap attraction fetching + Google Places enrichment |
| **Geo-Clustering Planner** | Pure-Python k-means spatial clustering + Gemini 2.5 Flash day themes & narrations |
| **Hidden Gem Score Formula** | Log-normalised formula: niche signal * sentiment - popularity penalty (7/7 tests passing) |
| **Embedded Chroma DB** | Vector store on disk (`niche_spots` + `itinerary_cache` collections) |
| **FastAPI Backend** | `/plan` (REST), `/plan/stream` (SSE), `/health`, `/export/pdf` stub |
| **Next.js 16 Frontend** | App Router, TypeScript, "Nocturnal Voyager" glassmorphism theme |
| **Interactive Live Wallpaper** | HTML5 canvas with global & Indian flight paths (Delhi, Mumbai, Jaipur, Goa, Bengaluru) |
| **Mapbox GL JS Map** | Dark navigation-night map with custom numbered amber & teal markers |

---

## Upcoming Phases

### Phase 2 — Niche Signal & Scoring
- Reddit scraping via public JSON API / PRAW (`r/travel`, `r/solotravel`, regional subs)
- Tavily blog search fallback
- VADER sentiment analysis on mention contexts
- Ranker Agent to blend popular + niche spots by `niche_weight`

### Phase 3 — Merged Pipeline + SSE + Routing
- Progressive SSE streaming (stream each `day_ready` event as it completes)
- OpenRouteService walk/transit times
- Open-Meteo per-day weather forecasting

### Phase 4 — Fine-Tuning (Local Narration Model)
- Curate CC-licensed travel dataset (Wikivoyage, Project Gutenberg)
- Unsloth + PEFT LoRA training on Llama 3.2 3B
- Deploy local Ollama model for atmospheric narrations

### Phase 5 — Conversational Editing
- Multi-turn state editing ("swap stop 3", "make day 2 more relaxed")
- Time-travel state recovery

### Phase 6 — Export & Polish
- Playwright headless PDF export
- Shareable itinerary URL slug
