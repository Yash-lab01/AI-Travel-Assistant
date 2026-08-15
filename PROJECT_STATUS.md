# WanderAI — Project Status

> *Last updated: 2026-08-15*

---

## What Is This Project?

WanderAI is a **multi-agent AI travel planner** built as a portfolio project to demonstrate three things that generic "ChatGPT + search API" demos don't:

1. **Tool-orchestrated reasoning** — a LangGraph state machine that plans, calls live tools (places, search, weather, routing), and adapts based on results. Not a single prompt-to-output call.

2. **A genuine ranking innovation** — a "hidden gem" score that cross-references mainstream popularity (Google Places review counts) against niche community sentiment (Reddit + travel blogs) to surface spots that are *actually* under-the-radar, not just under-reviewed.

3. **Applied fine-tuning** — a small local model (LoRA-tuned Llama 3B) trained on CC-licensed travel writing, used for final itinerary narration. This runs locally via Ollama — zero API cost, and the before/after comparison is documented.

**Framing line for interviews:**
> *"It's a multi-agent system where the hidden-gem scoring formula, the fine-tuned narration, and the cost-zero three-provider LLM routing are the actual engineering — the chat interface is just the surface."*

---

## Honest Feature Status

### ✅ Actually implemented and working

| Feature | What's real |
|---|---|
| **Project structure** | Full monorepo: `backend/` (FastAPI + Python) + `frontend/` (Next.js 16) |
| **Pydantic data schemas** | All core types: `TripRequest`, `Stop`, `DayPlan`, `Itinerary`, `NicheScore`, `AgentEvent` |
| **FastAPI backend** | Running at `localhost:8000`. Routes: `/plan`, `/plan/stream` (SSE), `/export/pdf` (stub), `/health` |
| **SSE streaming** | Backend streams `AgentEvent` JSON over HTTP SSE. Frontend renders in real-time |
| **LangGraph skeleton** | Graph compiles + runs with SQLite checkpointer (MemorySaver fallback) |
| **Hidden gem score formula** | Log-normalised formula: niche signal × sentiment − popularity penalty. **7/7 tests passing** |
| **Embedded Chroma** | Vector store on disk — no Docker. Two collections: `niche_spots` + `itinerary_cache` |
| **Frontend UI** | Two-panel layout: chat (left) + itinerary (right). Day tabs, stop cards, agent feed, prompt chips |
| **Design system** | "Nocturnal Voyager" (from StitchMCP) — deep navy, amber/teal, glassmorphism, animated background |
| **TypeScript types** | Frontend types mirror backend schemas 1:1 |
| **`intake_agent.py`** | Stub with correct interface — ready for Phase 1 LLM wiring |
| **`hidden_gem_score.py`** | Full formula implemented and unit tested |
| **`.env.example`** | All API keys documented and grouped |
| **README.md** | Architecture, formula, tech stack, setup instructions |

---

### ⚠️ Wired but mocked (framework exists, real logic not yet added)

| Feature | Current state | What's needed |
|---|---|---|
| **Intake Agent** | Returns hardcoded `TripRequest(destination="Lisbon", num_days=3)` | Groq Llama 3.1 8B slot-filling |
| **Planner Agent** | Returns a hardcoded 1-stop mock itinerary | Real OTM API calls + geo-clustering |
| **PDF export** | Returns `{"message": "coming soon"}` | Playwright headless render |
| **Chroma read/write** | Client initialised, collections created — nothing stored/queried yet | Wire into niche scrape tool |

---

### ❌ Not started yet

| Feature | Phase | Description |
|---|---|---|
| Real place data | Phase 1 | OpenTripMap API + Google Places enrichment |
| Interactive Mapbox map | Phase 1 | Stop markers, popups, day filter |
| Niche scraping (Reddit) | Phase 2 | PRAW mention extraction + VADER sentiment |
| Niche scraping (Tavily) | Phase 2 | Travel blog fallback |
| End-to-end scoring pipeline | Phase 2 | Scrape → score → Chroma store |
| Ranker Agent | Phase 3 | Blends popular + niche by `niche_weight` |
| Budget tracking | Phase 3 | Per-day cost totals |
| Routing (walk times) | Phase 3 | OpenRouteService |
| Weather tool | Phase 3 | Open-Meteo per-day forecast |
| Follow-up chat editing | Phase 5 | "Swap stop 3", "make day 2 more relaxed" |
| Fine-tuning dataset | Phase 4 | CC-licensed travel writing curation |
| LoRA training | Phase 4 | Unsloth + PEFT on Colab T4 |
| Local narration model | Phase 4 | Ollama-served fine-tuned Llama 3B |
| Playwright PDF export | Phase 6 | Pixel-perfect itinerary PDF |
| Shareable link | Phase 6 | UUID-based public itinerary URL |

---

## The Honest Summary

**The skeleton is 100% done. Zero core product features are live yet.**

The "core" features from a user perspective — real trip planning, real places, niche scoring, AI narration — are all stubs. What *is* real is the entire architectural foundation:

- The graph wires together
- Data contracts are stable and tested
- The scoring formula is correct and tested
- The frontend handles real SSE events, real itinerary JSON — just receiving mock data

Think of it as a film set: the walls, lighting, and camera angles are perfect — the actors (real LLM calls, real APIs) haven't been cast yet.

---

## Upcoming Phases — Detailed

### Phase 1 — Intake Agent + Real Place Data

**Intake Agent (Groq Llama 3.1 8B):**
- Structured JSON output: `{destination, num_days, budget_usd, niche_weight, travel_style, group_type, interests}`
- Multi-turn slot-filling: ask for missing info (budget, duration) before proceeding
- Ambiguity handling: unclear destination → ask for clarification

**OpenTripMap Tool:**
- `GET /en/places/radius?radius=5000&kinds=interesting_places&limit=30`
- Cache responses in Chroma by destination (TTL 24h) to stay in free tier
- Categories: attractions, restaurants, viewpoints, museums, parks, markets

**Google Places Enrichment:**
- Per spot: fetch photo, rating, review_count, opening hours
- Used for stop card images + popularity penalty in hidden gem score
- Free tier: only enrich top 20 spots

**Planner Agent (Gemini 2.5 Flash):**
- K-means clustering on lat/lon (k = num_days) to geographically group stops
- LLM assigns day theme, orders by opening hours, estimates walk times
- Output: structured `Itinerary` JSON

**Mapbox GL JS:**
- Dark navigation-night style map
- Amber markers = popular, teal markers = niche
- Clicking marker scrolls to stop card

**Exit criteria:** "3 days in Kyoto" → real 3-day itinerary with real photos + map.

---

### Phase 2 — Niche Signal & Scoring

**Three-tier scraping:**
- T1: PRAW (`r/solotravel`, `r/travel`, destination-specific subs) — extract place name mentions
- T2: Tavily search ("hidden gems {destination} travel blog 2024") — blog extraction
- T3: Chroma cache — pre-scraped data for popular destinations

**Scoring pipeline:**
```python
score = compute_hidden_gem_score(
    mention_count=spot.mention_count,
    avg_sentiment=VADER(mention_contexts),   # -1 to 1
    source_types=spot.sources,              # ["reddit", "tavily_blog"]
    google_review_count=spot.review_count,
    max_review_count_in_batch=max_reviews,
)
```

**Exit criteria:** Lisbon itinerary returns ≥2 stops with `is_niche=True`, score > 0.5, Reddit source attribution shown.

---

### Phase 3 — Merged Pipeline + SSE + Routing

- **Ranker Agent:** Blends popular + niche spots by `niche_weight` (0.0 → 1.0 slider)
- **Progressive SSE:** Stream each `day_ready` event as it completes — frontend renders progressively
- **Budget tracking:** Real `estimated_cost_usd` per stop, summed per day, shown in progress bar
- **OpenRouteService:** Walk/transit times between stops → `travel_time_from_prev_minutes`
- **Open-Meteo:** Day-matched weather forecast → `weather_note` on `DayPlan`

---

### Phase 4 — Fine-Tuning (The Differentiator)

**Dataset curation:**
- Sources: Wikivoyage (CC BY-SA), Project Gutenberg travel memoirs, 50 hand-authored examples
- Format: instruction-following pairs (stop details in → atmospheric narration out)

**Training (Unsloth + PEFT LoRA):**
- Base: `Llama-3.2-3B-Instruct`
- LoRA rank 16, 3 epochs, ~2h on free Colab T4
- 4-bit QLoRA for RAM efficiency

**Evaluation:**
- 20-sample blind preference test: base vs fine-tuned
- Metric: specificity, voice consistency, avoidance of generic phrases
- Results documented in `finetuning/eval_results.md`

**Deployment:**
- Export to GGUF → serve via Ollama locally
- LangGraph narration node: `ChatOllama(model="wanderai-narrator")`

---

### Phase 5 — Conversational Editing

- Intent classification: new trip | modify stop | change pace | change budget
- LangGraph time-travel: recover previous state if user asks to revert
- UI: follow-up input pre-filled with current itinerary context

---

### Phase 6 — Export & Polish

- Playwright headless PDF render with full styling (photos included)
- `?itinerary=<uuid>` shareable URL from SQLite
- Mapbox polyline routing overlay
- Mobile-responsive layout
- LangSmith trace link in UI footer during demos

---

## Running the Project

```powershell
# Terminal 1 — Backend
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open **http://localhost:3000**

```bash
# Tests
cd backend
cmd /c ".venv\Scripts\activate && python -m pytest tests\ -v"
# 7/7 passing
```
