# HANDOFF.md — Active Session Handoff

## 1. Current Session Context & User Directives
The user provided clear feedback on real user testing:
1. **Clarifying Questions in Chat**: The assistant should ask 2–3 contextual questions with clickable quick-reply chips inside the chat when given minimal prompts like *"3 day trip in Goa"*, while always offering a **"Plan with defaults now"** one-click button.
2. **Spatial Dispersion across Days**: Fix the 6km clustering issue for large regions/states (Goa, Rajasthan, Bali, etc.) by discovering POIs across diverse sub-regions (e.g. North Goa, Panjim, South Goa) and assigning distinct zones per day.
3. **Centered Studio & Side-by-Side Map Layout**: Overhaul the UI from a cramped left/right split into a large, centered conversational hub that smoothly unfolds into an expansive side-by-side Map + Timeline visualizer.
4. **Phase Ordering**: Phase 3 now encompasses Conversational Intake + Regional Dispersion + Centered UI + Weather & Routing. Phase 4 is Conversational Editing. Phase 5 is Fine-Tuning.

---

## 2. Immediate Actionable Steps for Phase 3 Execution

| Target File | Changes to Make |
|---|---|
| `backend/app/models/schemas.py` | Add `needs_clarification`, `clarification_questions`, `options` to schemas |
| `backend/app/agents/intake_agent.py` | Detect prompt completeness; return clarifying questions + option chips when underspecified unless forced |
| `backend/app/tools/places_tool.py` | Add regional/state awareness with adaptive search radius & sub-region centroids |
| `backend/app/tools/weather_tool.py` | Fetch free Open-Meteo forecasts by coordinates and date |
| `backend/app/tools/routing_tool.py` | Calculate realistic walking/transit times between sequential stops |
| `backend/app/graph/travel_graph.py` | Add conditional branch on `intake`: if `needs_clarification -> END` else `ranker -> planner -> END` |
| `frontend/src/components/ChatPanel.tsx` | Render interactive question chips, "Plan with defaults" button, and prominent centered chat UI |
| `frontend/src/app/page.tsx` & `globals.css` | Update studio layout to prominent centered conversational hub + wide side-by-side itinerary & map grid |
