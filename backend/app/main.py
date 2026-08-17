"""
FastAPI backend — AI Travel Assistant
Phase 0: skeleton with mock endpoints.
"""
import asyncio
import json
import uuid
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.models.schemas import (
    TripRequest, Itinerary, ChatRequest, AgentEvent
)
from app.graph.travel_graph import travel_graph
from app.vector_store.chroma_client import get_chroma_client

# ─── LangSmith tracing (set env vars to enable) ──────────────────────────────
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=<your key>
# LANGCHAIN_PROJECT=ai-travel-assistant


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up Chroma on startup
    get_chroma_client()
    print("[OK] Chroma vector store ready")
    print("[OK] LangGraph travel graph compiled")
    yield


app = FastAPI(
    title="AI Travel Assistant API",
    description="Multi-agent travel planning system with hidden-gem scoring and fine-tuned narration.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# ─── Plan (REST — full itinerary, no streaming) ───────────────────────────────

@app.post("/plan", response_model=Itinerary)
async def plan(request: ChatRequest):
    """
    Generate a full itinerary synchronously.
    Phase 0: returns mock data via the stub graph.
    """
    session_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "trip_request": None,
        "popular_stops_raw": [],
        "niche_spots_raw": [],
        "itinerary": None,
        "events": [],
        "session_id": session_id,
        "is_edit": request.existing_itinerary_id is not None,
        "edit_instruction": request.message if request.existing_itinerary_id else None,
    }

    result = await travel_graph.ainvoke(initial_state, config)

    if not result.get("itinerary"):
        raise HTTPException(status_code=500, detail="Itinerary generation failed.")

    return result["itinerary"]


# ─── Plan/Stream (SSE — streams AgentEvents then final itinerary) ─────────────

@app.post("/plan/stream")
async def plan_stream(request: ChatRequest):
    """
    Stream agent events via Server-Sent Events.
    Phase 0: streams mock events from the stub graph.
    """
    session_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "trip_request": None,
        "popular_stops_raw": [],
        "niche_spots_raw": [],
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
            await asyncio.sleep(0.05)

        if itinerary:
            yield f"event: itinerary\ndata: {itinerary.model_dump_json()}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Export PDF (stub — Phase 6) ──────────────────────────────────────────────

@app.get("/export/pdf/{itinerary_id}")
async def export_pdf(itinerary_id: str):
    """Phase 6: Playwright renders the itinerary view → PDF. Stub for now."""
    return {"message": "PDF export coming in Phase 6", "itinerary_id": itinerary_id}


# ─── Share slug (stub — Phase 6) ──────────────────────────────────────────────

@app.get("/trip/{slug}")
async def get_shared_trip(slug: str):
    """Phase 6: Return a shared itinerary by slug."""
    return {"message": "Shared trip view coming in Phase 6", "slug": slug}
