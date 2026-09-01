"""
FastAPI application entry point — Phase 3
Endpoints:
  POST /plan          - Synchronous trip planning (REST)
  POST /plan/stream   - Streaming trip planning with AgentEvents + Clarification (SSE)
  GET  /health        - Health check
  GET  /export/pdf    - PDF export stub
"""
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
import uuid
import json
import asyncio
import os
import re
from dotenv import load_dotenv

load_dotenv()

from app.models.schemas import (
    ChatRequest,
    Itinerary,
    AgentEvent,
    StopEditRequest,
    StopReorderRequest,
    StopFeedbackRequest,
    PackingListResponse,
)
from app.graph.travel_graph import travel_graph
from app.agents.editor_agent import editor_node
from app.vector_store.chroma_client import get_chroma_client
from app.db.history_store import (
    save_itinerary,
    get_all_histories,
    get_itinerary_by_id,
    delete_itinerary,
)
from app.tools.pdf_generator import generate_itinerary_pdf, generate_itinerary_html
from app.tools.ical_generator import generate_itinerary_ical
from app.tools.packing_list_generator import generate_smart_packing_list
from app.tools.routing_tool import calculate_sequential_transit_times
from app.db.feedback_store import record_stop_feedback

app = FastAPI(
    title="WanderAI API",
    description="Versatile Multi-Agent Travel Planner API",
    version="0.5.0",
)

# Allow Next.js frontend (localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ───────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.5.0"}


# ── Plan (REST) ──────────────────────────────────────────────────────────────
@app.post("/plan", response_model=Itinerary)
async def plan(request: ChatRequest):
    """Generate a full itinerary synchronously (bypassing clarification if requested)."""
    session_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "trip_request": None,
        "destination": request.destination,
        "num_days": request.num_days,
        "force_plan": request.force_plan,
        "clarification_answers": request.answers,
        "needs_clarification": False,
        "clarification_questions": [],
        "popular_stops_raw": [],
        "niche_spots_raw": [],
        "ranked_stops": [],
        "itinerary": None,
        "events": [],
        "session_id": session_id,
        "is_edit": request.existing_itinerary_id is not None or request.action is not None,
        "edit_instruction": request.message if (request.existing_itinerary_id or request.action) else None,
        "edit_intent": request.action,
        "target_day": request.target_day,
        "target_stop_id": request.target_stop_id,
        "target_stop_name": request.target_stop_name,
        "assistant_reply": None,
    }

    result = await travel_graph.ainvoke(initial_state, config)
    itinerary = result.get("itinerary")

    if not itinerary:
        raise HTTPException(status_code=400, detail="Itinerary generation requires clarification or failed.")

    # Auto-save to trip history
    try:
        save_itinerary(itinerary)
    except Exception as e:
        print(f"[history_store] Warning: Auto-save failed: {e}")

    return itinerary


# ── Plan/Stream (SSE — streams AgentEvents, Clarifications, and Itinerary) ───
@app.post("/plan/stream")
async def plan_stream(request: ChatRequest):
    """Stream agent events, interactive clarification questions, assistant messages, and final itinerary via SSE."""
    session_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "trip_request": None,
        "destination": request.destination,
        "num_days": request.num_days,
        "force_plan": request.force_plan,
        "clarification_answers": request.answers,
        "needs_clarification": False,
        "clarification_questions": [],
        "popular_stops_raw": [],
        "niche_spots_raw": [],
        "ranked_stops": [],
        "itinerary": None,
        "events": [],
        "session_id": session_id,
        "is_edit": request.existing_itinerary_id is not None or request.action is not None,
        "edit_instruction": request.message if (request.existing_itinerary_id or request.action) else None,
        "edit_intent": request.action,
        "target_day": request.target_day,
        "target_stop_id": request.target_stop_id,
        "target_stop_name": request.target_stop_name,
        "assistant_reply": None,
    }

    async def event_generator():
        result = await travel_graph.ainvoke(initial_state, config)
        events: list[AgentEvent] = result.get("events", [])
        itinerary: Itinerary | None = result.get("itinerary")
        assistant_reply: str | None = result.get("assistant_reply")

        for event in events:
            yield f"event: agent_event\ndata: {event.model_dump_json()}\n\n"
            await asyncio.sleep(0.04)

        if assistant_reply:
            yield f"event: assistant_message\ndata: {json.dumps({'message': assistant_reply})}\n\n"

        if itinerary:
            # Auto-save to trip history database
            try:
                save_itinerary(itinerary)
            except Exception as e:
                print(f"[history_store] Warning: Stream auto-save failed: {e}")

            yield f"event: itinerary\ndata: {itinerary.model_dump_json()}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Direct Stop Editing Endpoint (PATCH /plan/{itinerary_id}/stop) ───────────
@app.patch("/plan/{itinerary_id}/stop", response_model=Itinerary)
async def edit_itinerary_stop(itinerary_id: str, request: StopEditRequest):
    """
    Direct targeted stop modification (swap or remove) for UI quick action buttons.
    """
    config = {"configurable": {"thread_id": itinerary_id}}
    
    state_update = {
        "messages": [HumanMessage(content=f"{request.action} stop on Day {request.day_number}")],
        "is_edit": True,
        "edit_intent": f"{request.action}_stop",
        "target_day": request.day_number,
        "target_stop_id": request.stop_id,
        "target_stop_name": request.stop_name,
        "edit_instruction": request.custom_preference or f"{request.action} stop on Day {request.day_number}",
        "events": [],
    }

    result = await travel_graph.ainvoke(state_update, config)
    itinerary = result.get("itinerary")
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found or could not be modified.")
    
    # Save updated itinerary to history
    try:
        save_itinerary(itinerary)
    except Exception as e:
        print(f"[history_store] Warning: Edit auto-save failed: {e}")

    return itinerary


# ── Stop Reordering Endpoint (Phase 7) ──────────────────────────────────────
@app.post("/plan/{itinerary_id}/reorder", response_model=Itinerary)
async def reorder_itinerary_stops(itinerary_id: str, req: StopReorderRequest):
    """
    Reorder stops within a specific day and re-calculate sequential transit times.
    """
    itinerary = get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found.")

    target_day = next((d for d in itinerary.days if d.day_number == req.day_number), None)
    if not target_day:
        raise HTTPException(status_code=404, detail=f"Day {req.day_number} not found in itinerary.")

    stop_map = {s.id: s for s in target_day.stops}
    reordered_stops = [stop_map[sid] for sid in req.stop_ids if sid in stop_map]

    # If any stops were not in the reordered list, append them
    for s in target_day.stops:
        if s.id not in req.stop_ids:
            reordered_stops.append(s)

    # Recalculate sequential transit times
    updated_stops = calculate_sequential_transit_times(reordered_stops)
    target_day.stops = updated_stops

    # Update in database
    try:
        save_itinerary(itinerary)
    except Exception as e:
        print(f"[history_store] Warning: Reorder save failed: {e}")

    return itinerary


# ── User Feedback Endpoint (Phase 7) ────────────────────────────────────────
@app.post("/feedback")
async def submit_stop_feedback(feedback: StopFeedbackRequest):
    """
    Record user thumbs up/down rating on an individual stop.
    Saves to SQLite and appends to backend/data/user_feedback.jsonl.
    """
    try:
        result = record_stop_feedback(feedback)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {e}")


# ── Smart Packing List Endpoints (Phase 7) ──────────────────────────────────
@app.post("/trip/{itinerary_id}/packing-list", response_model=PackingListResponse)
async def get_packing_list_for_itinerary(itinerary_id: str):
    """
    Generate an activity- & weather-aware smart packing checklist for a saved trip.
    """
    itinerary = get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found.")

    return await generate_smart_packing_list(itinerary)


@app.post("/trip/packing-list", response_model=PackingListResponse)
async def get_packing_list_direct(itinerary: Itinerary):
    """
    Generate a smart packing list directly from an in-memory Itinerary payload.
    """
    return await generate_smart_packing_list(itinerary)


# ── iCalendar (.ics) Export Endpoints (Phase 7) ──────────────────────────────
@app.get("/export/ical/{itinerary_id}")
async def export_ical_by_id(itinerary_id: str):
    """
    Generate and stream an RFC 5545 .ics iCalendar file for Google/Apple/Outlook Calendar.
    """
    itinerary = get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found.")

    dest = itinerary.trip_request.destination if itinerary.trip_request else "Trip"
    safe_dest = re.sub(r'[^a-zA-Z0-9_-]', '_', dest)
    filename = f"WanderAI-{safe_dest}-{itinerary_id[:8]}.ics"

    ical_content = generate_itinerary_ical(itinerary)

    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@app.post("/export/ical")
async def export_ical_direct(itinerary: Itinerary):
    """
    Generate and stream an RFC 5545 .ics iCalendar file directly from an Itinerary payload.
    """
    dest = itinerary.trip_request.destination if itinerary.trip_request else "Trip"
    safe_dest = re.sub(r'[^a-zA-Z0-9_-]', '_', dest)
    short_id = (itinerary.id or "trip")[:8]
    filename = f"WanderAI-{safe_dest}-{short_id}.ics"

    ical_content = generate_itinerary_ical(itinerary)

    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


# ── Trip History Endpoints (Phase 4f) ─────────────────────────────────────────
@app.get("/history")
async def list_trip_history(limit: int = 50):
    """Return lightweight summaries of all saved trips."""
    return get_all_histories(limit=limit)


@app.post("/history")
async def save_trip_history(itinerary: Itinerary):
    """Explicitly save/upsert an itinerary into the history database."""
    saved_meta = save_itinerary(itinerary)
    return {"status": "saved", "trip": saved_meta}


@app.get("/history/{itinerary_id}", response_model=Itinerary)
async def get_trip_history_item(itinerary_id: str):
    """Retrieve full Itinerary JSON to restore a previous trip."""
    itinerary = get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Trip not found in history.")
    return itinerary


@app.delete("/history/{itinerary_id}")
async def delete_trip_history_item(itinerary_id: str):
    """Delete a saved itinerary from history."""
    deleted = delete_itinerary(itinerary_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Trip not found in history.")
    return {"status": "deleted", "id": itinerary_id}


# ── PDF Export Endpoints (Phase 6) ──────────────────────────────────────────
@app.get("/export/pdf/{itinerary_id}")
async def export_pdf_by_id(itinerary_id: str):
    """
    Generate and stream a high-fidelity PDF travel guide for a saved itinerary.
    """
    itinerary = get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found.")

    dest = itinerary.trip_request.destination if itinerary.trip_request else "Trip"
    safe_dest = re.sub(r'[^a-zA-Z0-9_-]', '_', dest)
    filename = f"WanderAI-{safe_dest}-{itinerary_id[:8]}.pdf"

    pdf_bytes = await generate_itinerary_pdf(itinerary)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@app.post("/export/pdf")
async def export_pdf_direct(itinerary: Itinerary):
    """
    Generate and stream a high-fidelity PDF travel guide directly from an Itinerary payload.
    """
    dest = itinerary.trip_request.destination if itinerary.trip_request else "Trip"
    safe_dest = re.sub(r'[^a-zA-Z0-9_-]', '_', dest)
    short_id = (itinerary.id or "trip")[:8]
    filename = f"WanderAI-{safe_dest}-{short_id}.pdf"

    pdf_bytes = await generate_itinerary_pdf(itinerary)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


# ── Shareable Itinerary Endpoint (Phase 6) ────────────────────────────────────
@app.get("/share/{slug_or_id}", response_model=Itinerary)
async def get_shared_trip(slug_or_id: str):
    """
    Retrieve an itinerary for public sharing / read-only viewing.
    """
    itinerary = get_itinerary_by_id(slug_or_id)
    if not itinerary:
        # Also check all histories in case slug is mapped
        histories = get_all_histories(limit=100)
        for h in histories:
            if h.get("id", "").startswith(slug_or_id) or slug_or_id in h.get("id", ""):
                found = get_itinerary_by_id(h["id"])
                if found:
                    return found
        raise HTTPException(status_code=404, detail="Shared trip not found.")
    return itinerary



