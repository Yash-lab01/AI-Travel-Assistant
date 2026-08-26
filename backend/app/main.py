"""
FastAPI application entry point — Phase 3
Endpoints:
  POST /plan          - Synchronous trip planning (REST)
  POST /plan/stream   - Streaming trip planning with AgentEvents + Clarification (SSE)
  GET  /health        - Health check
  GET  /export/pdf    - PDF export stub
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
import uuid
import json
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.models.schemas import ChatRequest, Itinerary, AgentEvent, StopEditRequest
from app.graph.travel_graph import travel_graph
from app.agents.editor_agent import editor_node
from app.vector_store.chroma_client import get_chroma_client
from app.db.history_store import (
    save_itinerary,
    get_all_histories,
    get_itinerary_by_id,
    delete_itinerary,
)

app = FastAPI(
    title="WanderAI API",
    description="Versatile Multi-Agent Travel Planner API",
    version="0.4.0",
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
    return {"status": "ok", "version": "0.4.0"}


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
    
    # Run edit through the travel graph in edit mode
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


# ── PDF Export Stub ──────────────────────────────────────────────────────────
@app.get("/export/pdf/{itinerary_id}")
async def export_pdf(itinerary_id: str):
    """Stub PDF export endpoint."""
    return {"message": "PDF export available in Phase 6", "itinerary_id": itinerary_id}

