# Current Project State
> Last updated: 2026-08-19

---

## Project Overview

**WanderAI** is a versatile multi-agent AI travel planner designed to plan complete, personalized day-by-day itineraries across any global or regional destination — seamlessly balancing iconic must-see sights, authentic hidden gems, budget constraints, and spatial pacing.

---

## What's Completed

### Phase 0 — Foundations (100% ✅)
- FastAPI backend with `/plan` (REST), `/plan/stream` (SSE), `/health`, `/export/pdf`
- LangGraph `StateGraph` with SQLite checkpointer (`data/checkpoints.db`) and JsonPlusSerializer
- All Pydantic schemas: `TripRequest → Stop → DayPlan → Itinerary → AgentEvent`
- Embedded Chroma vector store at `backend/data/chroma_db/` (`niche_spots` + `itineraries`)
- Log-normalised hidden gem scoring formula (7/7 unit tests passing)
- Next.js 16 frontend with "Nocturnal Voyager" dark design system
- Multi-section scrollable landing page & HTML5 Canvas Live Wallpaper
- Leaflet + CartoDB Dark Matter map integration (zero token / free)

### Phase 1 — Real Data Pipeline & Spatial Clustering (100% ✅)
- Intake Agent (Gemini 3.5 Flash / Groq slot extraction + robust regex fallback)
- Places Tool (Nominatim geocoding + OpenTripMap flat JSON parser + Google Places enrichment)
- Planner Agent (K-means++ coordinate clustering + Gemini 3.5 Flash destination-aware themes & narrations)

### Phase 2 — Niche Signal Scraping & Scoring Engine (100% ✅)
- Tavily travel search tool (`tavily_tool.py`) with blog & Reddit snippet extraction
- Reddit public discussion scraper (`reddit_tool.py`) with zero auth / zero key requirement
- Niche scraper & scoring pipeline (`niche_scraper.py`) with VADER sentiment intensity analysis
- Ranker Agent (`ranker_agent.py`) blending mainstream attractions and authentic hidden gems by `niche_weight`
- Guaranteed non-empty `ranked_stops` output — planner never bypasses the ranker
- 11/11 tests passing in pytest suite

### Phase 3 — Real-World Enhancements & UX Polish (100% ✅)
1. **Conversational Clarifications**: Detects brief prompts and asks 2–3 targeted questions with interactive chips, preserving destination across turns.
2. **Regional Multi-Zone Dispersion**: Queries distinct subzone centroids for states/regions (Goa, Rajasthan, Bali, Mumbai, Pune, Delhi, Kerala, Jaipur, Tokyo, Lisbon) for broad geographic day-by-day distribution.
3. **Transit Times & Weather**: Routing tool calculates sequential travel times; Open-Meteo provides live daily weather forecasts per day.
4. **Smart Currency Formatter**: Displays `₹ INR` for all Indian destinations and `$ USD` for international trips.
5. **Nocturnal Planning Studio UI**: Centered conversational studio unfolding into an interactive side-by-side Timeline + Map visualizer.
6. **Error-Proof Resiliency**: Safe LLM string extraction (`safe_extract_text`), guaranteed `k` day clustering, and safe Leaflet marker bounds.

### Phase 3 — Hardening Pass (100% ✅)
7. **K-means++**: Replaced index-seeded initialization — Day 1 no longer underpopulated. Post-clustering rebalance pass caps stop-count variance.
8. **Versioned Chroma Cache (`v4`)**: Old stale/mock data auto-bypassed. Cache writes only store `source="opentripmap"` stops. Increment `CACHE_VERSION` in `places_tool.py` on schema changes.
9. **Ranker Non-Empty Guarantee**: `ranker_node` always outputs `ranked_stops` (falls back to popular-only if niche scraper fails). `planner_node` logs `[WARNING]` on any bypass.
10. **Gemini Theme Fix**: Code-fence stripping before JSON parse; destination-aware fallback themes for Mumbai, Pune, Goa, Delhi, Jaipur, Kerala, Bali, Lisbon, Tokyo.
### Phase 4a — Image Integration & Visual Richness (100% ✅)
12. **Curated Destination Banners (`destination_images.py`)**: 25+ high-res landscape cover images for Indian and global destinations.
13. **3-Tier Sourcing Pipeline**: Google Places photos → Wikimedia Commons CC-licensed thumbnails → Unsplash curated photography fallback.
14. **Visual Day Banners & Itinerary Cover**: Full-bleed hero imagery for itinerary headers and day tabs with gradient overlays.
15. **StopCard Photographic Thumbnails**: Shimmer skeleton loading state, lazy loading, and robust `onError` fallback to category icons.
16. **Landing Page Destination Cards**: Visual prompt cards with photographic backgrounds and hover zoom animations.
17. **Map Marker Popup Thumbnails**: High-resolution image thumbnails embedded in Leaflet marker popups.

---

## What's Next

### Phase 4b — Multi-Turn Conversational Editing (NEXT 🔜)
- Intent classifier node: `new_trip` | `edit_stop` | `adjust_pace` | `change_budget`
- LangGraph checkpoint recovery for stop-level editing without full replan
- UI "Swap / Remove / Tell me more" quick-action buttons on stop cards
- `PATCH /plan/{id}/stop` endpoint for targeted stop replacement

### Phase 5 — Local Fine-Tuned Narration Model (LoRA)
- LoRA fine-tuning on Llama 3.2 3B with Unsloth + PEFT (Colab T4)
- Local Ollama deployment for zero-latency atmospheric narration

### Phase 6 — Export, Sharing & Production Polish
- Playwright PDF export, shareable URL slugs, Leaflet polyline route overlay

---

## Reference Documents
- [`docs/IMAGE_INTEGRATION.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/docs/IMAGE_INTEGRATION.md) — **NEW** — Full image implementation spec (3-tier sourcing, frontend changes, schema updates, what NOT to do).
- [`docs/TROUBLESHOOTING_AND_MISTAKES.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/docs/TROUBLESHOOTING_AND_MISTAKES.md) — Persistent log of 9 known pitfalls, model quirks, and rules for what NOT to do.
- [`.context/PROJECT_CONTEXT.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/.context/PROJECT_CONTEXT.md) — Architecture, active model names, Chroma path, coding conventions.
- [`.context/TASKS.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/.context/TASKS.md) — Granular phase task checklist.
- [`.context/HANDOFF.md`](file:///c:/Users/yashp/Desktop/AI%20Travel%20Assistant/.context/HANDOFF.md) — Latest session bug fixes & immediate next steps.
