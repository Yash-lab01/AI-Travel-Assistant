# WanderAI — Multi-Agent AI Travel Planner

> **A conversational multi-agent AI travel planner** that crafts complete, personalized day-by-day itineraries for any global or regional destination — balancing iconic landmarks, authentic local hidden gems, budget, pacing, and spatial coherence through live multi-agent reasoning.

![Next.js](https://img.shields.io/badge/Next.js_16-black?style=flat-square&logo=nextdotjs)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-7C3AED?style=flat-square)
![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Chroma](https://img.shields.io/badge/ChromaDB-FF6B35?style=flat-square)

---

## What Makes This Different

Most AI travel demos are a thin wrapper around a single LLM prompt. WanderAI is an autonomous multi-agent state machine where each agent has a distinct role, real tools, and spatial awareness:

1. **Dynamic LLM-Powered Clarifying Questions** — Detects brief or underspecified prompts ("3 days in Goa") and uses Gemini 2.0 Flash to generate 2–3 *contextual* preference questions tailored to exactly what the user mentioned. "3 days in Kyoto, anime culture" gets completely different chips than "3 days in Kyoto, Zen temples and ramen." Curated static templates for well-known destinations (Goa, Mumbai, Lisbon, Rajasthan) override for maximum speed; unknown global destinations get fully LLM-generated questions.

2. **Hidden Gem Engine** — A log-normalized scoring formula cross-references mainstream popularity (Google Places review counts) against niche community sentiment (Reddit, travel blogs via Tavily) to surface spots that are *actually* under-the-radar, not just under-reviewed.

3. **K-means++ Spatial Clustering** — Groups POIs into geographically coherent daily segments with maximally-spread centroid initialization, preventing Day 1 from being a tiny pocket while Days 2–3 cover the whole city.

4. **Regional Multi-Zone Dispersion** — For wide destinations (Goa, Rajasthan, Bali, Mumbai, Kerala), the planner queries distinct sub-zone centroids per day, ensuring each day explores a genuinely different part of the destination.

5. **Live Data at Runtime** — Every itinerary fetches real-time weather forecasts (Open-Meteo), realistic transit times (haversine routing), live attraction data (OpenTripMap), and 4-tier real photography (Wikipedia REST → Wikimedia Commons → Unsplash → Pexels).

6. **Full Export & Share Suite** — Playwright PDF brochure export, shareable public `/trip/[slug]` URLs, and a share modal with 1-click WhatsApp, X, and Email integrations.

7. **Smart ₹/$ Currency** — Detects Indian destinations and displays all cost estimates in `₹ INR`; international trips use `$ USD`.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│               Next.js 16 Frontend  (Nocturnal Voyager UI)            │
│   ChatPanel (SSE streaming)  │  ItineraryView  │  MapView (Leaflet)  │
└──────────────────┬───────────────────────────────────────────────────┘
                   │  REST / SSE
┌──────────────────▼───────────────────────────────────────────────────┐
│              FastAPI + Uvicorn  (async, port 8000)                   │
│    /plan (REST)  │  /plan/stream (SSE)  │  /health  │  /export/pdf  │
└──────────────────┬───────────────────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────────────────┐
│                    LangGraph State Machine                            │
│                                                                       │
│   [intake_node]  ──►  [ranker_node]  ──►  [planner_node]  ──►  END  │
│                                                                       │
│   Intake Agent         Ranker Agent         Planner Agent            │
│   • Gemini 3.5 Flash   • Fetches OTM        • K-means++ clustering   │
│     structured slots     popular stops        (k = num_days)         │
│   • Regex fallback     • Discovers niche    • Destination-aware      │
│   • Clarifying Qs        gems concurrently    day themes (Gemini)    │
│   • Destination          via niche_scraper  • Per-stop narrations    │
│     persistence        • Blends by           • Routing + weather     │
│                          niche_weight         attachment              │
└──────────────────┬───────────────────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────────────────┐
│                         Tool & Data Layer                            │
│                                                                       │
│  places_tool      Nominatim (geocoding) + OpenTripMap (flat JSON)    │
│                   + Google Places (photos, ratings, review count)    │
│                   + Versioned ChromaDB cache (v4, OTM-only writes)   │
│                                                                       │
│  niche_scraper    Reddit public JSON API + Tavily blog search        │
│                   + VADER sentiment + log-normalized gem score       │
│                   + ChromaDB niche_spots cache                       │
│                                                                       │
│  routing_tool     Haversine sequential transit time estimation       │
│  weather_tool     Open-Meteo free daily forecast per DayPlan         │
└──────────────────┬───────────────────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────────────────┐
│                      Storage & Inference                             │
│   ChromaDB (embedded, ./data/chroma_db/)  — niche_spots + itineraries│
│   SQLite (./data/checkpoints.db)          — LangGraph checkpoints    │
│   Gemini 3.5 Flash (Google AI Studio)    — themes & narrations       │
│   Groq (openai/gpt-oss-20b)             — fast slot-filling          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Hidden Gem Score Formula

```python
hidden_gem_score = clamp(
    (min(mention_count, 20) / 20) * ((avg_sentiment + 1) / 2)   # niche signal strength
  + (0.2 if source_diversity >= 2 else 0)                        # cross-platform bonus
  - log(review_count + 1) / log(max_review_count + 1),          # popularity penalty (log-normalised)
  min=0.0, max=1.0
)
```

- **Log-normalization** prevents 10k vs 50k reviews from looking equally "popular"
- **Source diversity bonus** rewards spots mentioned independently on multiple platforms (Reddit + blog)
- **Sentiment weighting** prioritizes enthusiastic recommendations over casual mentions
- Unit-tested in `backend/tests/test_scoring.py` — **7/7 tests passing**

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| **Orchestration** | LangGraph `StateGraph` (async) | Deterministic node routing, SQLite checkpoints |
| **Primary LLM** | Gemini 3.5 Flash (Google AI Studio) | Day themes, narrations, clarifying questions |
| **Slot-filling LLM** | Groq `openai/gpt-oss-20b` | Fast structured JSON extraction, regex fallback |
| **Place Data** | OpenTripMap (flat JSON) + Google Places | Attractions, categories, photos, ratings |
| **Geocoding** | Nominatim (OpenStreetMap) | Free, no key required |
| **Niche Discovery** | Reddit public API + Tavily search | Zero-auth community signal extraction |
| **Sentiment** | VADER (`vaderSentiment`) | Offline, zero-latency sentiment scoring |
| **Vector Store** | ChromaDB (embedded, `./data/chroma_db/`) | Versioned cache (`v4`), no Docker needed |
| **Weather** | Open-Meteo | Free daily forecast per day plan |
| **Routing** | Haversine (`routing_tool.py`) | Realistic walk/transit time between stops |
| **Backend** | FastAPI + Uvicorn | Async, SSE streaming, PDF export |
| **Frontend** | Next.js 16 (App Router) + TypeScript | React 19, Vanilla CSS |
| **Map** | Leaflet + CartoDB Dark Matter tiles | 100% free, no Mapbox token/credit card needed |
| **Live Wallpaper** | HTML5 Canvas 2D | Global flight arcs, Indian travel hubs, aurora glows |
| **Design System** | "Nocturnal Voyager" | Playfair Display + Outfit + Sora, glassmorphism |
| **Currency** | `currency.ts` smart formatter | `₹ INR` for Indian cities, `$ USD` international |

---

## Key Design Decisions

### Why Leaflet + CartoDB over Mapbox?
Mapbox requires a credit card even on the free tier. CartoDB Dark Matter tiles are fully free with no authentication — zero friction for local dev and portfolio demos.

### Why embedded ChromaDB over Docker Chroma?
On-disk embedded Chroma runs with zero infrastructure. Collections persist in `backend/data/chroma_db/`. Cache entries are versioned (`CACHE_VERSION="v4"` in `places_tool.py`) — incrementing this constant auto-invalidates all stale data on the next request.

### Why K-means++ over standard K-means?
Standard index-seeded k-means consistently placed Day 1's centroid in a tiny geographic pocket for dense Indian city POI distributions. K-means++ seeds centroids proportional to squared distance from existing seeds — maximally spreading them across the destination to produce balanced day clusters.

### Why does the Ranker always run before the Planner?
The Ranker is the single source of stops for the Planner. It fetches OTM popular stops and niche scraped gems concurrently, blends them by `niche_weight`, and guarantees a non-empty `ranked_stops` list. This ensures the Planner never bypasses niche blending by fetching its own OTM data.

---

## Project Structure

```
AI Travel Assistant/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point (SSE + REST + PDF export)
│   │   ├── agents/
│   │   │   ├── intake_agent.py      # Conversational slot-filling + clarifying questions
│   │   │   ├── ranker_agent.py      # Popular + niche blending (guaranteed non-empty output)
│   │   │   └── planner_agent.py     # K-means++ clustering + Gemini themes + narrations
│   │   ├── tools/
│   │   │   ├── places_tool.py       # OTM + Google Places + versioned Chroma cache
│   │   │   ├── niche_scraper.py     # Reddit + Tavily + VADER + hidden gem scoring
│   │   │   ├── routing_tool.py      # Sequential haversine transit times
│   │   │   ├── weather_tool.py      # Open-Meteo daily forecast
│   │   │   ├── reddit_tool.py       # Reddit public JSON scraper (zero auth)
│   │   │   └── tavily_tool.py       # Tavily blog search tool
│   │   ├── graph/
│   │   │   ├── state.py             # TravelGraphState TypedDict
│   │   │   └── travel_graph.py      # LangGraph compilation + routing
│   │   ├── models/schemas.py        # Pydantic data contracts (single source of truth)
│   │   ├── scoring/hidden_gem_score.py  # Log-normalized gem formula
│   │   └── vector_store/chroma_client.py  # Embedded Chroma singleton
│   ├── data/
│   │   ├── checkpoints.db           # LangGraph SQLite checkpoints
│   │   └── chroma_db/               # ChromaDB on-disk store
│   └── tests/                       # pytest suite (11/11 passing)
├── frontend/
│   └── src/
│       ├── app/page.tsx             # Landing + Planning Studio layout
│       ├── app/globals.css          # Nocturnal Voyager design tokens
│       ├── components/
│       │   ├── ChatPanel.tsx        # SSE streaming chat + clarification chips
│       │   ├── ItineraryView.tsx    # Day tabs + stop cards + summary stats
│       │   ├── MapView.tsx          # Leaflet + CartoDB dark map
│       │   ├── AgentEventFeed.tsx   # Real-time agent thought stream
│       │   └── TravelLiveWallpaper.tsx  # HTML5 Canvas animated flight paths
│       ├── utils/currency.ts        # ₹/$ smart formatter
│       └── types/index.ts           # TypeScript mirrors of schemas.py
├── .context/                        # LLM continuity memory
│   ├── PROJECT_CONTEXT.md           # Architecture + conventions
│   ├── TASKS.md                     # Phase roadmap checklist
│   └── HANDOFF.md                   # Session bug log + next steps
├── docs/
│   ├── CURRENT_STATE.md             # Phase completion status
│   └── TROUBLESHOOTING_AND_MISTAKES.md  # Known pitfalls + what NOT to do
└── stop-servers.ps1                 # Kill ports 3000 + 8000 on Windows
```

---

## Setup & Running

### Prerequisites
- Python 3.12+
- Node.js 18+
- (Optional) API keys for live data — **the app runs fully in zero-key fallback mode without any keys**

### 1. Configure Environment
```bash
cp .env.example .env
# Fill in any keys you have — all are optional:
# GOOGLE_AI_STUDIO_API_KEY  → Gemini 3.5 Flash themes & narrations
# GROQ_API_KEY              → Fast LLM slot-filling
# OPENTRIPMAP_API_KEY       → Real attraction data (otherwise uses rich mocks)
# GOOGLE_PLACES_API_KEY     → Photo & rating enrichment
# TAVILY_API_KEY            → Blog search for niche gems
```

### 2. Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **[http://localhost:3000](http://localhost:3000)**

### 4. Running Tests
```bash
cd backend
.venv\Scripts\Activate.ps1
pytest tests/ -v
# Expected: 11/11 tests passing
```

### 5. Kill Servers (Windows)
```powershell
.\stop-servers.ps1
```

---

## Phases & Roadmap

| Phase | Status | Summary |
|---|---|---|
| **0 — Foundations** | ✅ Complete | FastAPI, LangGraph, Chroma, Pydantic schemas, Next.js 16, Nocturnal Voyager UI |
| **1 — Real Data Pipeline** | ✅ Complete | OTM flat JSON parser, Nominatim geocoding, Google Places enrichment, K-means++ clustering |
| **2 — Niche Discovery** | ✅ Complete | Reddit scraper, Tavily search, VADER sentiment, hidden gem score, Ranker Agent |
| **3 — Conversational UX + Hardening** | ✅ Complete | Clarifying questions, regional subzones, routing, weather, ₹ currency, versioned cache, k-means++ |
| **4 — Multi-Turn Editing** | 🔜 Next | Intent classifier (edit/swap/adjust), LangGraph checkpoint recovery, stop-level patching |
| **5 — Local Fine-Tuned Narration** | ⏳ Planned | LoRA on Llama 3.2 3B (Unsloth + PEFT), local Ollama deployment |
| **6 — Export & Production** | ⏳ Planned | Playwright PDF export, shareable URL slugs, route polyline overlay |

---

## Out of Scope
- Direct flight/hotel booking transactions (compliance & financial scope)
- Visa/consular document validation
- Real-time live pricing from OTAs (Booking.com, MakeMyTrip, etc.)
