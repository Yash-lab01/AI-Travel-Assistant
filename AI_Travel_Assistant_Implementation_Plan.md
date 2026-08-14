# AI Travel Assistant — Implementation Plan
### Niche-Aware, Multi-Agent, Fine-Tuned Travel Planning System

**Author:** Yash Bhawar
**Purpose:** Portfolio-differentiating, product-facing AI agent demonstrating conversational orchestration, live web/tool-use reasoning, hidden-gem ranking logic, and local model fine-tuning (LoRA).

---

## 1. Project Thesis (for interviewers)

Most "AI travel planner" demos are a thin prompt wrapper around a search API. This project is deliberately built to demonstrate three things that generic clones don't:

1. **Tool-orchestrated reasoning** — a LangGraph agent that plans, calls live tools (search, places, weather, scraping), and adapts based on results, rather than a single prompt-to-output call.
2. **A genuine ranking innovation** — a "hidden gem" score that cross-references mainstream popularity signals (Google Places) against niche community sentiment (Reddit/blogs) to surface spots that are *actually* under-the-radar, not just under-reviewed.
3. **Applied fine-tuning** — a small local model (LoRA-tuned) distilled from a larger model's writing style, used for the final itinerary narration. This is the piece most candidates skip, and it's the one most worth showing.

Framing line for interviews: *"It's not a travel chatbot with a search tool bolted on — it's a multi-agent system where the ranking logic and the fine-tuned narration layer are the actual engineering, and the chat interface is just the surface."*

---

## 2. Feature Scope (Final)

### Core (must-ship)
- Conversational trip intake (destination, dates, budget, pace, style, group type)
- Popular attraction retrieval (Google Places)
- Niche/hidden-gem retrieval + scoring (Reddit + blog scraping → sentiment/rarity score)
- Day-by-day itinerary generation with time slots, travel time between stops, budget running total
- Real photos per stop
- Fine-tuned local model for itinerary narration ("local guide" voice)
- Shareable itinerary export (webpage + PDF)
- Chat-based iteration ("swap day 2 afternoon for something more relaxed")

### Stretch (only if core is solid and stable)
- Weather-aware re-suggestion (e.g. flag outdoor day if rain forecast)
- AI-illustrated postcard summary per stop (image-gen)
- Multi-city trip chaining
- Collaborative trip editing (shareable link, multiple users comment/vote on stops)
- Price-trend estimation for flights/hotels (mock/sandbox API, not real booking)

### Explicitly out of scope (state this clearly to interviewers — shows judgment)
- Real payment/booking integration (compliance/liability scope creep, not the point of the demo)
- Visa/travel document logic (too regulatory-heavy, low engineering value)

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Next.js 15 Frontend                    │
│         Chat UI · Itinerary View · Map View · Export          │
└───────────────────────────┬────────────────────────────────┘
                             │ SSE / REST
┌───────────────────────────▼────────────────────────────────┐
│                      FastAPI Backend                          │
│              Session state · Auth (optional) · Export         │
└───────────────────────────┬────────────────────────────────┘
                             │
┌───────────────────────────▼────────────────────────────────┐
│                  LangGraph Orchestration Layer                │
│                                                                 │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐      │
│   │ Intake Agent │──▶│ Planner Agent │──▶│ Ranker Agent │      │
│   └──────────────┘   └──────┬───────┘   └──────┬───────┘      │
│                              │                   │              │
│                    ┌─────────▼─────────┐ ┌───────▼────────┐   │
│                    │  Tool Layer         │ │ Scoring Engine │   │
│                    │  - search_tool      │ │ (popularity vs │   │
│                    │  - places_tool      │ │  niche signal) │   │
│                    │  - weather_tool     │ └────────────────┘   │
│                    │  - niche_scrape_tool│                      │
│                    └─────────────────────┘                      │
│                              │                                  │
│                    ┌─────────▼─────────┐                        │
│                    │ Narration Agent    │                        │
│                    │ (fine-tuned local  │                        │
│                    │  LoRA model)       │                        │
│                    └────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                     ▼
   Qdrant (niche         Groq/Cloud API        Ollama (local,
   spot embeddings)      (primary reasoning)   fine-tuned model)
```

**Model split rationale:**
- Cloud API (Groq 70B or equivalent) handles tool-calling and multi-step reasoning — small local models are not reliable enough for this yet.
- Fine-tuned local model is used *only* for final narration generation, where consistency of voice matters more than reasoning depth. This is a deliberate, defensible architectural choice — not local-first dogma, not cloud-only laziness.

---

## 4. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | LangGraph | Consistent with existing portfolio stack; explicit graph makes the multi-agent story demoable |
| Primary reasoning LLM | Groq (Llama 3.3 70B) | Fast, cheap, strong tool-calling |
| Narration LLM | Local LoRA-tuned Llama 3.1 8B / Mistral 7B via Ollama | The fine-tuning centerpiece |
| Fine-tuning framework | Unsloth + PEFT (LoRA) | Fast, low-VRAM fine-tuning, well-documented |
| Search/extraction | Tavily API | LLM-oriented search results, clean extraction |
| Structured place data | Google Places API | Ratings, hours, photos, coordinates — the "popular" signal |
| Niche signal | Reddit (PRAW) + targeted blog scraping (Playwright) | The "hidden gem" signal |
| Vector store | Qdrant | Already in use elsewhere in portfolio; stores niche-spot text for retrieval/scoring |
| Backend | FastAPI | Consistent with existing projects |
| Frontend | Next.js 15 | UX polish is the point of this project — should look distinct from Streamlit tools |
| Export | WeasyPrint or Puppeteer (HTML → PDF) | Clean shareable itinerary output |
| Deployment | Docker Compose (backend + Qdrant + frontend), Vercel for frontend if split | Matches existing infra experience |

---

## 5. Phase-Wise Build Plan

### Phase 0 — Foundations & Contracts
Goal: nothing "smart" yet — get the skeleton and data contracts right so every later phase has a stable interface to build against.

- Define core data schemas: `TripRequest`, `Stop`, `DayPlan`, `Itinerary`, `NicheScore`
- Set up FastAPI project skeleton with a placeholder `/plan` endpoint returning mock data
- Set up Next.js 15 frontend skeleton with a chat panel + empty itinerary panel wired to the mock endpoint
- Provision Qdrant instance (Docker) and Google Places / Tavily API keys
- Repo structure, `.env` management, README stub for interviewer framing

**Exit criteria:** frontend can send a trip request and render a hardcoded mock itinerary end-to-end.

---

### Phase 1 — Intake & Popular Recommendation Path
Goal: get the "boring but necessary" mainstream path working before adding the differentiator.

- Build Intake Agent: multi-turn slot-filling (destination, dates, budget, pace, style, group type) with graceful handling of partial/ambiguous input
- Integrate Google Places API: fetch top attractions, restaurants, and lodging areas for the destination
- Build a naive Planner Agent: arrange popular stops into a day-by-day structure (no ranking intelligence yet, just sane grouping by geography/opening hours)
- Render itinerary in frontend with real photos from Places

**Exit criteria:** you can input a real destination and get a coherent, popular-attraction-based itinerary with photos.

---

### Phase 2 — Niche Signal & Hidden-Gem Scoring Engine
Goal: this is the core differentiator — build it as its own testable module, not buried inside the planner.

- Build `niche_scrape_tool`: targeted Reddit search (PRAW) for destination-specific threads + recommendation posts; optionally 2–3 curated travel blog sources via Playwright
- Extract candidate place mentions from scraped text (LLM extraction pass)
- Embed and store candidate spots + supporting text in Qdrant
- Build the **scoring engine**: combine (a) mention frequency/sentiment from niche sources with (b) mainstream visibility from Places (review count as a proxy) into a single "hidden gem score" — explicitly define the formula/logic so it's explainable, not a black box
- Unit-test the scoring logic on 2–3 known destinations with manually sanity-checked expected outcomes

**Exit criteria:** given a destination, the system produces a ranked list of niche spots with a defensible, explainable score — independent of the rest of the pipeline.

---

### Phase 3 — Merge Planner (Popular + Niche) & Ranker Agent
Goal: combine Phase 1 and Phase 2 into one coherent Planner Agent.

- Extend Planner Agent to blend popular and niche stops per day based on user's stated style preference (e.g. "mostly popular, one hidden gem per day" vs "mostly niche")
- Add travel-time estimation between stops (Google Distance Matrix or OpenRouteService) to keep days geographically sane
- Add budget tracking across the itinerary (rough cost estimates per stop/meal, running total vs stated budget)
- Add weather tool integration (optional at this stage) to flag outdoor-heavy days

**Exit criteria:** full itinerary generation works end-to-end with real popular + niche data, geography-aware ordering, and budget tracking — narration is still generic/templated at this point.

---

### Phase 4 — Fine-Tuning Pipeline (LoRA Narration Model)
Goal: the centerpiece. Treat this as its own mini-project with its own documentation.

- Generate training data: use the cloud LLM to produce a large batch (hundreds of examples) of high-quality "local guide" style itinerary narration across varied destinations/stop types
- Curate/clean the dataset; define the target voice explicitly (tone, sentence length, avoid generic phrasing) so the fine-tune has a clear target, not just "sound nicer"
- Fine-tune a small base model (Llama 3.1 8B or Mistral 7B) using Unsloth + LoRA on the curated dataset
- Evaluate: side-by-side comparison of base model vs fine-tuned model on held-out stops (blind preference test, document the results — this is strong interview material)
- Serve the fine-tuned model locally via Ollama; wire it in as the Narration Agent, replacing templated text

**Exit criteria:** itinerary narration is generated by your own fine-tuned model, with a documented before/after comparison proving the fine-tune improved output quality.

---

### Phase 5 — Chat-Based Iteration & Editing
Goal: make the assistant feel like an agent you converse with, not a one-shot generator.

- Support follow-up edits via chat: swap a stop, change pace for one day, replace a niche spot, adjust budget
- Maintain conversation + itinerary state across turns (LangGraph state persistence)
- Handle edge cases gracefully: infeasible requests (budget too low for destination), ambiguous destinations, no niche data found for very small towns

**Exit criteria:** a user can iteratively refine a generated itinerary through natural conversation without starting over.

---

### Phase 6 — Export, Polish & Stretch Features
Goal: ship-quality output and portfolio presentation.

- Build shareable itinerary export: clean webpage view + PDF export (WeasyPrint/Puppeteer)
- UI polish pass: map view of the itinerary, day tabs, responsive design
- Add stretch features if time allows, in priority order: weather-aware re-suggestion → AI-illustrated postcards → multi-city chaining → collaborative editing
- Write the project README with: architecture diagram, the hidden-gem scoring explanation, the fine-tuning before/after results, and a short demo GIF/video

**Exit criteria:** a polished, demoable, documented project ready to link from the portfolio.

---

### Phase 7 — Evaluation & Documentation (Interview Readiness)
Goal: turn the build into a story, matching the way you've documented past projects (writing up failures alongside wins).

- Document what didn't work: e.g. first scoring formula that over-weighted mention count, prompt strategies that failed for niche extraction, fine-tuning runs that overfit or under-improved
- Write a short "engineering decisions" section: why cloud reasoning + local narration split, why this scoring formula, why these data sources
- Prepare a 2-minute walkthrough script for interviews, mirroring the framing line in Section 1

---

## 6. Suggested Repo Structure

```
ai-travel-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── agents/
│   │   │   ├── intake_agent.py
│   │   │   ├── planner_agent.py
│   │   │   ├── ranker_agent.py
│   │   │   └── narration_agent.py
│   │   ├── tools/
│   │   │   ├── places_tool.py
│   │   │   ├── search_tool.py
│   │   │   ├── weather_tool.py
│   │   │   └── niche_scrape_tool.py
│   │   ├── scoring/
│   │   │   └── hidden_gem_score.py
│   │   ├── models/
│   │   │   └── schemas.py
│   │   └── graph/
│   │       └── travel_graph.py
│   ├── finetuning/
│   │   ├── generate_training_data.py
│   │   ├── train_lora.py
│   │   ├── evaluate_finetune.py
│   │   └── dataset/
│   └── requirements.txt
├── frontend/
│   └── (Next.js 15 app)
├── docker-compose.yml
└── README.md
```

---

## 7. Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Reddit/blog scraping gets rate-limited or blocked | Cache aggressively, keep scraping scope narrow (curated subreddits/sites), add graceful fallback to Places-only mode |
| Fine-tuning doesn't visibly improve output | Document it anyway with the blind comparison — an honest negative result with analysis is still strong portfolio material |
| Hidden-gem score feels arbitrary | Keep the formula simple and explainable; log inputs/outputs so it's demoable and defensible, not a black box |
| Scope creep into booking/payments | Explicitly out of scope (Section 2) — state this proactively in interviews as a scoping decision, not a limitation |
