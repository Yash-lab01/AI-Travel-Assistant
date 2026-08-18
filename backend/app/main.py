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

from app.models.schemas import ChatRequest, Itinerary, AgentEvent
from app.graph.travel_graph import travel_graph
from app.vector_store.chroma_client import get_chroma_client

app = FastAPI(
    title="WanderAI API",
    description="Versatile Multi-Agent Travel Planner API",
    version="0.3.0",
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
    return {"status": "ok", "version": "0.3.0"}


# ── Plan (REST) ──────────────────────────────────────────────────────────────
@app.post("/plan", response_model=Itinerary)
async def plan(request: ChatRequest):
    """Generate a full itinerary synchronously (bypassing clarification if requested)."""
    session_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "trip_request": None,
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
        "is_edit": request.existing_itinerary_id is not None,
        "edit_instruction": request.message if request.existing_itinerary_id else None,
    }

    result = await travel_graph.ainvoke(initial_state, config)

    if not result.get("itinerary"):
        raise HTTPException(status_code=400, detail="Itinerary generation requires clarification or failed.")

    return result["itinerary"]


# ── Plan/Stream (SSE — streams AgentEvents, Clarifications, and Itinerary) ───
@app.post("/plan/stream")
async def plan_stream(request: ChatRequest):
    """Stream agent events, interactive clarification questions, and final itinerary via SSE."""
    session_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "trip_request": None,
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
        "is_edit": request.existing_itinerary_id is not None,
        "edit_instruction": request.message if request.existing_itinerary_id else None,
    }

    async def event_generator():
        result = await travel_graph.ainvoke(initial_state, config)
        events: list[AgentEvent] = result.get("events", [])
        itinerary: Itinerary | None = result.get("itinerary")

        for event in events:
            yield f"event: agent_event\ndata: {event.model_dump_json()}\n\n"
            await asyncio.sleep(0.04)

        if itinerary:
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


# ── PDF Export Stub ──────────────────────────────────────────────────────────
@app.get("/export/pdf/{itinerary_id}")
async def export_pdf(itinerary_id: str):
    """Stub PDF export endpoint."""
    return {"message": "PDF export available in Phase 6", "itinerary_id": itinerary_id}
