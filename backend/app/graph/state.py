"""
LangGraph state definition for the travel planning graph.
All agents share and mutate this state object.
"""
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from app.models.schemas import (
    TripRequest, Itinerary, NicheScore, AgentEvent, Stop, ClarificationQuestion
)


class TravelGraphState(TypedDict):
    # Conversation history (LangGraph managed)
    messages: Annotated[list, add_messages]

    # Slot-filled trip parameters (built by Intake Agent)
    trip_request: Optional[TripRequest]
    destination: Optional[str]                             # Preserved destination across turns
    num_days: Optional[int]                                # Preserved num_days across turns

    # Clarification state
    force_plan: bool                                       # Bypass clarification if True
    clarification_answers: Optional[dict[str, str]]        # Answers selected by user
    needs_clarification: bool                              # Set to True by Intake if prompt is brief
    clarification_questions: list[ClarificationQuestion]   # Generated clarifying questions & chips

    # Raw candidates from tools (before ranking)
    popular_stops_raw: list[dict]                          # From OpenTripMap + Google Places
    niche_spots_raw: list[NicheScore]                      # From niche_scrape_tool + scoring engine
    ranked_stops: list[Stop]                               # Curated & blended stops from Ranker Agent

    # Final planned + narrated itinerary
    itinerary: Optional[Itinerary]

    # Streaming events emitted during graph execution
    events: list[AgentEvent]

    # Session context
    session_id: str
    is_edit: bool                                          # True if this is a follow-up edit, not a fresh plan
    edit_instruction: Optional[str]
