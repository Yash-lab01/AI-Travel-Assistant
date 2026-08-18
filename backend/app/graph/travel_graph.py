"""
LangGraph travel planning graph — Phase 3
Wires: intake_agent (conditional) -> ranker_agent -> planner_agent -> END
"""
from langgraph.graph import StateGraph, END
import sqlite3
import os

_SQLITE_AVAILABLE = False
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
    _SQLITE_AVAILABLE = True
except ImportError:
    from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import TravelGraphState
from app.agents.intake_agent import intake_node
from app.agents.ranker_agent import ranker_node
from app.agents.planner_agent import planner_node

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "checkpoints.db")


def route_intake(state: TravelGraphState) -> str:
    """If intake determines user needs clarification, stop and return clarifying questions."""
    if state.get("needs_clarification"):
        return END
    return "ranker"


def build_graph():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if _SQLITE_AVAILABLE:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        serde = JsonPlusSerializer(allowed_msgpack_modules=[("app.models.schemas", "*")])
        checkpointer = SqliteSaver(conn, serde=serde)
    else:
        checkpointer = MemorySaver()

    builder = StateGraph(TravelGraphState)
    builder.add_node("intake",  intake_node)
    builder.add_node("ranker",  ranker_node)
    builder.add_node("planner", planner_node)

    builder.set_entry_point("intake")
    builder.add_conditional_edges(
        "intake",
        route_intake,
        {
            END: END,
            "ranker": "ranker",
        }
    )
    builder.add_edge("ranker", "planner")
    builder.add_edge("planner", END)

    return builder.compile(checkpointer=checkpointer)


travel_graph = build_graph()
