"""
Intake Agent — Phase 1
Stub: passes raw message through as a minimal TripRequest.
Real multi-turn slot-filling implemented in Phase 1.
"""
from app.graph.state import TravelGraphState
from app.models.schemas import TripRequest, AgentEvent, TravelStyle, TravelPace, GroupType


def intake_node(state: TravelGraphState) -> dict:
    events = list(state.get("events", []))
    events.append(AgentEvent(
        event_type="agent_start",
        agent="intake_agent",
        message="Parsing your trip requirements...",
    ))

    # Phase 1 will use an LLM (Groq Llama 3.1 8B) for structured slot-filling.
    # For now, return a stub TripRequest.
    user_msg = ""
    messages = state.get("messages", [])
    if messages:
        last = messages[-1]
        user_msg = last.content if hasattr(last, "content") else str(last)

    stub_request = TripRequest(
        destination="Lisbon",
        num_days=3,
        budget_usd=1500,
        travel_style=TravelStyle.balanced,
        niche_weight=0.5,
        pace=TravelPace.moderate,
        group_type=GroupType.solo,
        interests=[],
        raw_message=user_msg,
    )

    events.append(AgentEvent(
        event_type="agent_step",
        agent="intake_agent",
        message=f"Destination identified: {stub_request.destination} ({stub_request.num_days} days)",
    ))

    return {"trip_request": stub_request, "events": events}
