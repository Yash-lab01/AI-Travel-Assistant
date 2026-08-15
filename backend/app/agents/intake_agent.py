"""
Intake Agent — Phase 1
Uses Groq Llama 3.1 8B for structured slot-filling from natural language.

Falls back to a rule-based parser if Groq API key is not set or hits a rate limit.
"""
from __future__ import annotations
import json
import os
import re
from app.graph.state import TravelGraphState
from app.models.schemas import (
    TripRequest, AgentEvent, TravelStyle, TravelPace, GroupType
)

GROQ_KEY = os.getenv("GROQ_API_KEY", "")

SYSTEM_PROMPT = """You are a travel planning assistant. Extract trip details from the user's message and return ONLY valid JSON.

Required fields:
- destination (string): city/country name
- num_days (integer): number of days, default 3
- budget_usd (float or null): total budget in USD, null if not specified
- niche_weight (float 0-1): 0=all popular sights, 1=all hidden gems, 0.5=balanced. Default 0.5
- travel_style (string): one of "cultural", "adventure", "relaxed", "foodie", "balanced". Default "balanced"
- pace (string): one of "slow", "moderate", "fast". Default "moderate"
- group_type (string): one of "solo", "couple", "family", "friends". Default "solo"
- interests (array of strings): e.g. ["art", "food", "history"]. Empty array if none mentioned

Example output:
{"destination":"Lisbon","num_days":3,"budget_usd":1200,"niche_weight":0.7,"travel_style":"cultural","pace":"moderate","group_type":"solo","interests":["history","food"]}

Return ONLY the JSON object, no explanation."""


async def _extract_with_groq(user_message: str) -> dict | None:
    """Call Groq Llama 3.1 8B for structured slot extraction."""
    if not GROQ_KEY:
        return None

    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=GROQ_KEY,
            temperature=0.1,
            max_tokens=256,
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]

        response = await llm.ainvoke(messages)
        raw = response.content.strip()

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None

    except Exception as e:
        print(f"[intake_agent] Groq extraction failed: {e}")
        return None


def _extract_rule_based(text: str) -> dict:
    """Fallback: simple regex-based extraction when no Groq key."""
    text_lower = text.lower()

    # Destination: look for "in <place>" or "to <place>"
    destination = "Unknown Destination"
    dest_match = re.search(
        r'(?:in|to|visit|trip to|travel to|days? in)\s+([A-Z][a-zA-Z\s]+?)(?:\s*,|\s+for|\s+on|\s*$)',
        text, re.IGNORECASE
    )
    if dest_match:
        destination = dest_match.group(1).strip().title()

    # Days
    num_days = 3
    days_match = re.search(r'(\d+)\s*(?:days?|nights?)', text_lower)
    if days_match:
        num_days = int(days_match.group(1))

    # Budget
    budget_usd = None
    budget_match = re.search(r'\$\s*(\d[\d,]*)', text)
    if budget_match:
        budget_usd = float(budget_match.group(1).replace(",", ""))

    # Niche weight
    niche_weight = 0.5
    if any(w in text_lower for w in ["hidden gem", "niche", "local", "off the beaten", "underrated", "secret"]):
        niche_weight = 0.75
    elif any(w in text_lower for w in ["popular", "tourist", "famous", "landmark", "classic"]):
        niche_weight = 0.25

    # Travel style
    travel_style = "balanced"
    if any(w in text_lower for w in ["food", "eat", "cuisine", "restaurant"]):
        travel_style = "foodie"
    elif any(w in text_lower for w in ["history", "museum", "culture", "art", "architecture"]):
        travel_style = "cultural"
    elif any(w in text_lower for w in ["adventure", "hike", "outdoor", "nature"]):
        travel_style = "adventure"
    elif any(w in text_lower for w in ["relax", "slow", "chill", "beach", "peaceful"]):
        travel_style = "relaxed"

    # Group type
    group_type = "solo"
    if "couple" in text_lower or "partner" in text_lower or "romantic" in text_lower:
        group_type = "couple"
    elif "family" in text_lower or "kids" in text_lower or "children" in text_lower:
        group_type = "family"
    elif "friends" in text_lower or "group" in text_lower:
        group_type = "friends"

    # Pace
    pace = "moderate"
    if any(w in text_lower for w in ["slow", "relaxed", "leisurely", "easy"]):
        pace = "slow"
    elif any(w in text_lower for w in ["fast", "packed", "full", "intensive", "busy"]):
        pace = "fast"

    return {
        "destination":    destination,
        "num_days":       num_days,
        "budget_usd":     budget_usd,
        "niche_weight":   niche_weight,
        "travel_style":   travel_style,
        "pace":           pace,
        "group_type":     group_type,
        "interests":      [],
    }


def _dict_to_trip_request(data: dict, raw_message: str) -> TripRequest:
    """Convert extracted dict to validated TripRequest, clamping/defaulting bad values."""
    return TripRequest(
        destination=str(data.get("destination", "Unknown")).strip() or "Unknown",
        num_days=max(1, min(int(data.get("num_days", 3)), 14)),
        budget_usd=float(data["budget_usd"]) if data.get("budget_usd") else None,
        niche_weight=max(0.0, min(float(data.get("niche_weight", 0.5)), 1.0)),
        travel_style=_safe_enum(TravelStyle, data.get("travel_style", "balanced"), TravelStyle.balanced),
        pace=_safe_enum(TravelPace, data.get("pace", "moderate"), TravelPace.moderate),
        group_type=_safe_enum(GroupType, data.get("group_type", "solo"), GroupType.solo),
        interests=list(data.get("interests", [])),
        raw_message=raw_message,
    )


def _safe_enum(enum_class, value: str, default):
    try:
        return enum_class(value)
    except (ValueError, KeyError):
        return default


async def intake_node(state: TravelGraphState) -> dict:
    """
    Phase 1 intake node:
    1. Try Groq Llama 3.1 8B for structured extraction
    2. Fall back to rule-based regex parser
    3. Emit events throughout
    """
    events = list(state.get("events", []))
    messages = state.get("messages", [])

    user_msg = ""
    if messages:
        last = messages[-1]
        user_msg = last.content if hasattr(last, "content") else str(last)

    events.append(AgentEvent(
        event_type="agent_start",
        agent="intake_agent",
        message="Understanding your trip requirements...",
    ))

    # Try Groq first
    extracted = None
    if GROQ_KEY:
        events.append(AgentEvent(
            event_type="agent_step",
            agent="intake_agent",
            message="Parsing with Groq Llama 3.1 8B...",
        ))
        extracted = await _extract_with_groq(user_msg)

    # Rule-based fallback
    if not extracted:
        events.append(AgentEvent(
            event_type="agent_step",
            agent="intake_agent",
            message="Extracting trip details...",
        ))
        extracted = _extract_rule_based(user_msg)

    trip_request = _dict_to_trip_request(extracted, user_msg)

    niche_label = (
        "hidden gems focus" if trip_request.niche_weight > 0.65
        else "popular sights focus" if trip_request.niche_weight < 0.35
        else "balanced mix"
    )

    events.append(AgentEvent(
        event_type="agent_step",
        agent="intake_agent",
        message=(
            f"Got it! {trip_request.destination}, {trip_request.num_days} days"
            + (f", ${trip_request.budget_usd:,.0f} budget" if trip_request.budget_usd else "")
            + f", {niche_label}."
        ),
    ))

    return {"trip_request": trip_request, "events": events}
