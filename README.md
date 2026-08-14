# AI Travel Assistant

> **A multi-agent AI travel planner** that surfaces hidden gems alongside popular attractions — powered by LangGraph, Gemini 2.5 Flash, Groq, and a fine-tuned local narration model.

---

## What Makes This Different

Most AI travel demos are a thin wrapper around a search API. This project is built to demonstrate three concrete engineering contributions:

1. **Tool-orchestrated reasoning** — a LangGraph state machine that plans, calls live tools (search, places, Reddit, weather, routing), and adapts based on results. Not a single prompt-to-output call.

2. **A genuine ranking innovation** — a "hidden gem" score that cross-references mainstream popularity signals (Google Places review counts) against niche community sentiment (Reddit, travel blogs) to surface spots that are *actually* under-the-radar, not just under-reviewed. Formula is explicit, log-normalised, and unit-tested.

3. **Applied fine-tuning** — a small local model (LoRA-tuned Llama 3B) trained on CC-licensed travel writing, used for final itinerary narration. The fine-tuned voice runs locally via Ollama — no API cost, no latency, and the before/after comparison is documented in the repo.

> *"It's a multi-agent system where the hidden-gem scoring formula, the fine-tuned narration, and the cost-zero three-provider LLM routing are the actual engineering — the chat interface is just the surface, and LangSmith makes every agent decision visible in real-time."*

---

## Architecture

```
Next.js 15 Frontend (Chat UI · Itinerary View · Map · Export)
         │ SSE / REST
FastAPI Backend (Session state · SSE streaming · PDF export)
         │
LangGraph Orchestration Layer
   ├── Intake Agent        (Groq Llama 3.1 8B — slot-filling)
   ├── Planner Agent       (Gemini 2.5 Flash — tool-calling, structured JSON)
   ├── Ranker Agent        (Gemini 2.5 Flash — hidden-gem scoring, blending)
   └── Narration Agent     (Local LoRA model via Ollama)
         │
   Tool Layer
   ├── places_tool         (OpenTripMap primary + Google Places enrichment)
   ├── niche_scrape_tool   (PRAW T1 → Tavily T2 → Chroma cache T3)
   ├── weather_tool        (Open-Meteo, free)
   └── routing_tool        (OpenRouteService, free)
         │
   ├── Chroma (embedded vector store — niche spot embeddings, no Docker)
   ├── Gemini 2.5 Flash (Google AI Studio — free tier, ~1,500 RPD)
   ├── Groq (Llama 3.3 70B fallback / Llama 3.1 8B slot-filling)
   └── Ollama (local fine-tuned narration model)
```

**LangSmith** traces every agent step and tool call in real-time — pull it up during a demo to show the full graph execution trail.

---

## Hidden Gem Score Formula

```python
hidden_gem_score = (
    (min(mention_count, 20) / 20) × ((avg_sentiment + 1) / 2)   # niche signal
  + 0.2 if source_diversity >= 2 else 0                          # cross-platform bonus
  - log(review_count + 1) / log(max_review_count + 1)           # popularity penalty (log-normalised)
) clamped to [0, 1]
```

- **Log-normalisation** prevents 10k vs 50k reviews looking equally "popular"
- **Source diversity bonus** rewards spots mentioned across Reddit AND travel blogs
- **Sentiment weight** means enthusiastic mentions count more than vague ones
- Formula is unit-tested in `backend/tests/test_scoring.py`

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Orchestration | LangGraph | State machine, time-travel debug, LangSmith tracing |
| Primary LLM | Gemini 2.5 Flash | Free AI Studio tier, best tool-calling quality |
| Slot-filling LLM | Groq Llama 3.1 8B | 14,400 RPD free — high-volume, cheap steps |
| Fallback LLM | Groq Llama 3.3 70B | ~1,000 RPD free — 429 fallback chain |
| Narration LLM | Local LoRA via Ollama | Fine-tuned on CC-licensed travel writing |
| Fine-tuning | Unsloth + PEFT (LoRA) | Low-VRAM, Google Colab T4 compatible |
| Search | Tavily API | Niche signal T2 fallback + general search |
| Place data | OpenTripMap (primary) + Google Places (enrichment) | OTM is free + cacheable |
| Niche signal | PRAW (Reddit) → Tavily → Chroma cache | Three-tier, demo never fails |
| Vector store | Chroma (embedded) | No Docker dependency, same talking points as Qdrant |
| Observability | LangSmith | Full graph trace visible in real-time demo |
| Backend | FastAPI + SSE | Streaming agent events to frontend |
| Frontend | Next.js 15 | App Router, TypeScript |
| Map | Mapbox GL JS | Generous free tier, better styling than Google Maps |
| Export | Playwright PDF | Pixel-perfect UI render, no WeasyPrint CSS fidelity issues |

---

## Setup

### 1. Clone & configure
```bash
git clone <repo>
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Backend
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### 4. (Optional) Enable LangSmith tracing
In `.env`, set:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<your key>
```
Then open [smith.langchain.com](https://smith.langchain.com) during a run to see the full graph trace.

---

## Build Phases

| Phase | Status | Description |
|---|---|---|
| 0 — Foundations | ✅ | Schemas, FastAPI skeleton, Next.js skeleton, Chroma, LangSmith config |
| 1 — Popular path | 🔲 | Intake Agent (LLM slot-filling), OpenTripMap, Planner Agent, Mapbox |
| 2 — Niche scoring | 🔲 | PRAW + Tavily + Chroma, hidden gem score, unit tests |
| 3 — Merge + SSE | 🔲 | Ranker Agent, SSE streaming, budget tracking, routing |
| 4 — Fine-tuning | 🔲 | Dataset curation, Unsloth LoRA, before/after eval |
| 5 — Chat editing | 🔲 | Follow-up turn handling, state persistence, edge cases |
| 6 — Export & polish | 🔲 | Playwright PDF, shareable link, UI polish, Mapbox polyline |
| 7 — Documentation | 🔲 | Engineering decisions, failure log, interview walkthrough |

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Fine-Tuning

See `backend/finetuning/` for:
- `curate_dataset.py` — CC-licensed data ingestion + hand-example formatting
- `train_lora.py` — Unsloth + LoRA training script (runs on free Colab T4)
- `evaluate_finetune.py` — blind before/after preference test

Training data uses only CC BY-SA licensed sources (Wikivoyage, Project Gutenberg) and hand-authored examples — no outputs from closed-model APIs.

---

## Out of Scope

- Real payment/booking integration (compliance scope creep, not the engineering point)
- Visa/travel document logic (regulatory-heavy, low engineering value)
