"""
LangGraph state definition for the travel planning graph.
All agents share and mutate this state object.
"""
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from app.models.schemas import TripRequest, Itinerary, NicheScore, AgentEvent


class TravelGraphState(TypedDict):
    # Conversation history (LangGraph managed)
    messages: Annotated[list, add_messages]

    # Slot-filled trip parameters (built by Intake Agent)
    trip_request: Optional[TripRequest]

    # Raw candidates from tools (before ranking)
    popular_stops_raw: list[dict]       # From OpenTripMap + Google Places
    niche_spots_raw: list[NicheScore]   # From niche_scrape_tool + scoring engine

    # Final planned + narrated itinerary
    itinerary: Optional[Itinerary]

    # Streaming events emitted during graph execution
    events: list[AgentEvent]

    # Session context
    session_id: str
    is_edit: bool   # True if this is a follow-up edit, not a fresh plan
    edit_instruction: Optional[str]
