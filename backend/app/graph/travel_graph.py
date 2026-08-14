"""
LangGraph travel planning graph — wires all agents together.
Phase 0: stub nodes that emit mock events. Real logic added in Phase 1+.
"""
from langgraph.graph import StateGraph, END
import sqlite3
import os

_SQLITE_AVAILABLE = False
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    _SQLITE_AVAILABLE = True
except ImportError:
    from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import TravelGraphState
from app.models.schemas import AgentEvent, Itinerary, DayPlan, Stop, TripRequest
import uuid
from datetime import datetime


# ─── Stub agent nodes ────────────────────────────────────────────────────────

def intake_node(state: TravelGraphState) -> dict:
    """Phase 0 stub: echo back a mock TripRequest."""
    events = state.get("events", [])
    events.append(AgentEvent(
        event_type="agent_start",
        agent="intake_agent",
        message="Parsing your trip requirements...",
    ))
    # Real slot-filling in Phase 1
    mock_request = TripRequest(
        destination="Lisbon",
        num_days=3,
        budget_usd=1500,
        raw_message=state["messages"][-1].content if state.get("messages") else "",
    )
    return {"trip_request": mock_request, "events": events}


def planner_node(state: TravelGraphState) -> dict:
    """Phase 0 stub: return a hardcoded mock itinerary."""
    events = state.get("events", [])
    events.append(AgentEvent(
        event_type="agent_step",
        agent="planner_agent",
        message="Building your day-by-day itinerary...",
    ))

    mock_stop = Stop(
        id=str(uuid.uuid4()),
        name="Belém Tower",
        category="attraction",
        description="Iconic 16th-century tower on the Tagus river.",
        lat=38.6916,
        lon=-9.2159,
        duration_minutes=60,
        estimated_cost_usd=8.0,
        photo_urls=[],
        is_niche=False,
    )
    mock_day = DayPlan(
        day_number=1,
        theme="Historic Lisbon",
        stops=[mock_stop],
        daily_cost_estimate_usd=50.0,
    )
    mock_itinerary = Itinerary(
        id=str(uuid.uuid4()),
        trip_request=state["trip_request"],
        days=[mock_day],
        total_cost_estimate_usd=150.0,
        created_at=datetime.utcnow().isoformat(),
    )
    events.append(AgentEvent(
        event_type="itinerary_ready",
        agent="planner_agent",
        message="Your itinerary is ready!",
    ))
    return {"itinerary": mock_itinerary, "events": events}


# ─── Graph assembly ───────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "checkpoints.db")


def build_graph():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if _SQLITE_AVAILABLE:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        checkpointer = SqliteSaver(conn)
    else:
        checkpointer = MemorySaver()

    builder = StateGraph(TravelGraphState)
    builder.add_node("intake", intake_node)
    builder.add_node("planner", planner_node)

    builder.set_entry_point("intake")
    builder.add_edge("intake", "planner")
    builder.add_edge("planner", END)

    return builder.compile(checkpointer=checkpointer)


travel_graph = build_graph()
