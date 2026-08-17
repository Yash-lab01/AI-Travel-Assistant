# WanderAI — Versatile Multi-Agent Travel Planner

> **A versatile multi-agent AI travel planner** that crafts complete, personalized day-by-day itineraries — whether you want must-see iconic landmarks, authentic hidden gems, or the perfect curated blend of both. Powered by LangGraph, Gemini 2.5 Flash, Groq, OpenTripMap, and a fine-tuned local narration model.

---

## What Makes This Different

Most AI travel demos are a thin wrapper around a single search prompt. WanderAI is engineered as an autonomous multi-agent state machine that plans, discovers, ranks, and clusters trips across any global or regional destination:

1. **Tool-Orchestrated Multi-Agent Reasoning** — A deterministic LangGraph state machine where specialized agents (Intake slot-filling, Place Discovery, Spatial Clustering, Thematic Storytelling) query live tools (OpenTripMap, Google Places, Reddit, weather, routing) and adapt dynamically.

2. **Versatile Planning with Hidden Gem Engine** — Seamlessly plan classic sightseeing trips, balanced vacations, or deep off-the-beaten-path expeditions. Our log-normalized scoring formula cross-references mainstream popularity signals (Google Places review counts) against niche community sentiment (Reddit, travel blogs) to surface spots that are *actually* under-the-radar, not just under-reviewed.

3. **Spatial Geo-Clustering & Pacing** — Pure-Python k-means coordinate clustering groups attractions into seamless, walking-optimized daily segments without exhausting cross-city zig-zagging.

4. **Applied Fine-Tuning** — A small local model (LoRA-tuned Llama 3B) trained on CC-licensed travel writing, used for evocative stop narration. Runs locally via Ollama with zero API latency.

---

## Architecture

```
Next.js 16 Frontend (Nocturnal Voyager UI · Chat · Itinerary · Mapbox GL JS)
         │  SSE / REST
FastAPI Backend (Session state · SSE streaming · PDF export)
         │
LangGraph Orchestration Layer
   ├── Intake Agent        (Groq Llama 3.1 8B — structured slot-filling)
   ├── Planner Agent       (K-means geo-clustering + Gemini 2.5 Flash day themes)
   ├── Ranker Agent        (Blends popular sights + hidden gems by niche_weight)
   └── Narration Agent     (Local LoRA model via Ollama)
         │
   Tool & Data Layer
   ├── places_tool         (Nominatim geocoding + OpenTripMap + Google Places)
   ├── niche_scrape_tool   (Reddit JSON API + Tavily blog search + Chroma cache)
   ├── weather_tool        (Open-Meteo, free)
   └── routing_tool        (OpenRouteService, free)
         │
   ├── Chroma (embedded vector store — destination cache & niche spots)
   ├── Gemini 2.5 Flash (Google AI Studio — themes & narrations)
   ├── Groq (Llama 3.1 8B — ultra-fast slot-filling)
   └── Ollama (local fine-tuned narration model)
```

---

## Hidden Gem Score Formula

```python
hidden_gem_score = (
    (min(mention_count, 20) / 20) * ((avg_sentiment + 1) / 2)   # niche signal
  + (0.2 if source_diversity >= 2 else 0)                         # cross-platform bonus
  - log(review_count + 1) / log(max_review_count + 1)            # popularity penalty (log-normalised)
) clamped to [0, 1]
```

- **Log-normalisation** prevents 10k vs 50k reviews looking equally "popular".
- **Source diversity bonus** rewards spots mentioned across multiple independent platforms.
- **Sentiment weighting** prioritizes enthusiastic recommendations over casual mentions.
- Formula is unit-tested in `backend/tests/test_scoring.py` (7/7 tests passing).

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Orchestration | LangGraph (async) | State machine, time-travel debug, LangSmith tracing |
| Primary LLM | Gemini 2.5 Flash | Free AI Studio tier, rich theme & narration generation |
| Slot-filling LLM | Groq Llama 3.1 8B | Free tier, high-volume fast slot-filling with regex fallback |
| Place Data | OpenTripMap + Google Places | Attractions, category mapping, ratings, and photo enrichment |
| Geocoding | Nominatim | Free OpenStreetMap geocoding |
| Vector Store | Chroma (embedded) | On-disk destination caching, zero Docker requirement |
| Backend | FastAPI + Uvicorn | Async endpoints, Server-Sent Events (SSE) streaming |
| Frontend | Next.js 16 (App Router) | TypeScript, Nocturnal Voyager glassmorphic design system |
| Live Wallpaper | HTML5 Canvas | Global flight paths, Indian travel hubs, aurora glows |
| Map | Mapbox GL JS | Dark navigation-night style, custom amber/teal markers |

---

## Setup & Running

### 1. Configure Environment
```bash
cp .env.example .env
# Optional: Add your API keys for live LLMs and Mapbox
```

### 2. Backend
```bash
cd backend
.venv\Scripts\Activate.ps1   # Windows PowerShell
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### 4. Running Tests
```bash
cd backend
.venv\Scripts\pytest tests\ -v
```

---

## Out of Scope
- Direct flight/hotel booking transactions (compliance & financial scope creep)
- Visa/consular document validation
