# HANDOFF.md — Active Session Handoff
> Last updated: 2026-09-02

## 1. Bugs Diagnosed & Resolved (All Sessions)

1. **`AttributeError: 'list' object has no attribute 'strip'` in LLM Invocations**: `safe_extract_text()` added to `intake_agent.py`, `planner_agent.py`, `niche_scraper.py`.
2. **OpenTripMap Flat JSON vs GeoJSON Parser Miss**: Parser updated; regional centroids added for all major cities.
3. **Frontend Day Switching & Map Crash on Tab Click**: Strict k-cluster guarantee; safe `validActiveDay` indexing; lat/lon validation.
4. **Chroma Cache Serving Stale Mock Stops**: `CACHE_VERSION` system at **v6** in `places_tool.py`.
5. **K-means Day 1 Underpopulated**: Replaced with K-means++ initialization + post-clustering rebalance.
6. **Ranker Agent Bypassed**: `ranker_node` now guarantees never-empty `ranked_stops`.
7. **Day Themes Always Show Generic Fallback**: Code-fence stripping + destination-aware fallback themes.
8. **Wikipedia Exact Title Miss — Generic Category Images**: 4-tier image cascade (Wikipedia REST → Generator Search → Wikimedia Commons → Unsplash/Pexels). Cache bumped to v6.
9. **Leaflet `fitBounds` Error on initial render**: `invalidateSize()` + 50ms `setTimeout` defer + identical-coord fallback.
10. **Page Auto-Scrolling to Chat on Load**: Internal container scroll in `AgentEventFeed.tsx`/`ChatPanel.tsx` + `scrollRestoration = 'manual'` in `page.tsx`.
11. **Quick-edit chips broke the trip (Phase 7)**: Chips routed through `externalPrompt` → new trip with no context. Fixed by adding `externalEditInstruction` prop to `ChatPanel` so `existing_itinerary_id` is always sent.
12. **Leaflet polyline crash `TypeError: Cannot read undefined 'x'` (Phase 7)**: Polylines drawn before `invalidateSize()`. Fixed by moving polyline construction inside the 50ms `setTimeout`.

---

## 2. Documentation Updated

- ✅ `.context/TASKS.md` — Phase 7 section added (7A bugs, 7B dynamic clarifications, 7C planned)
- ✅ `.context/HANDOFF.md` — This file (fully current as of 2026-09-02)
- ✅ `.context/PROJECT_CONTEXT.md` — Dynamic clarification architecture documented
- ✅ `docs/COMPREHENSIVE_AUDIT_AND_ROADMAP.md` — Overkill features removed; Phase 7 roadmap refined for portfolio
- ✅ `README.md` — Updated feature list to include Phase 7 changes

---

## 3. Current Working State

- **Backend**: FastAPI `http://127.0.0.1:8000` running with `--reload`.
- **Frontend**: Next.js 16 `http://localhost:3000`, 0 TypeScript errors.
- **Pytest**: 31/31 tests passing.
- **Dynamic Clarifications (Phase 7B)**: `_generate_dynamic_clarification_questions()` in `intake_agent.py` — Gemini 2.0 Flash → Groq Llama 3.1 8B → static fallback chain. Questions are now prompt-specific.
- **Quick-edit chips fix (Phase 7A)**: `externalEditInstruction` prop routes edits with correct `existing_itinerary_id`.
- **Polyline crash fix (Phase 7A)**: Polylines now drawn inside `setTimeout` after `invalidateSize()`.
- **PDF Export (Phase 6)**: `GET /export/pdf/{id}` & `POST /export/pdf`. Playwright Chromium — **must install via `python -m playwright install chromium`**.
- **Shareable Public Trips (Phase 6)**: `/trip/[slug]` + `ShareModal` + `GET /share/{slug}`.
- **Sequential Route Polylines (Phase 6)**: Dual-layer glowing polylines in `MapView.tsx`.
- **Local LoRA Travel Narrator (Phase 5)**: `ml/ollama_narrator.py` zero-latency client.
- **Trip History (Phase 4f)**: SQLite + `localStorage` + `TripHistoryPanel` drawer.
- **Multi-Turn Editing (Phase 4e)**: `editor_agent.py` + StopCard actions (Swap, Remove, Tell Me More) + quick-edit chips.

---

## 4. Phase 7 Next Steps

**7C — UI Polish (not yet started):**
- Concrete time-slot scheduling per stop (09:30 AM – 11:00 AM)
- `dnd-kit` drag-and-drop reordering
- Framer Motion animations on stop state changes
- Skeleton shimmer loading states
- React error boundaries + SSE timeout
- Empty history panel state
- User feedback (👍/👎) → `ml/dataset/user_feedback.jsonl`
- Dietary filter chips
- Smart packing list generator
- `.ics` calendar export
- Google Maps navigation deep links

---

## 5. Completed Project Milestone Summary

Phases 0–6 fully implemented and tested. Phase 7A and 7B complete. Phase 7C in progress.
