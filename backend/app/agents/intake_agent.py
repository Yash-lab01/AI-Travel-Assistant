"""
Intake Agent — Phase 3
Extracts structured TripRequest from freeform messages using Gemini 3.5 Flash / Groq with robust regex fallback.
Includes conversational clarification logic: detects underspecified requests and generates
contextual clarifying questions with clickable chips, while preserving destination across turns.
"""
from __future__ import annotations
import json
import re
import os
from typing import Optional
from langchain_core.messages import HumanMessage

from app.models.schemas import (
    TripRequest, TravelStyle, TravelPace, GroupType, AgentEvent,
    ClarificationQuestion, ClarificationOption
)
from app.graph.state import TravelGraphState

GOOGLE_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")

# ── Destination-Specific Clarification Templates ─────────────────────────────
DESTINATION_QUESTIONS: dict[str, list[dict]] = {
    "goa": [
        {
            "id": "goa_vibe",
            "question": "Which coastal vibe are you looking for in Goa?",
            "category": "region_vibe",
            "options": [
                {"label": "North Goa — Beaches & Nightlife", "value": "North Goa (beaches/nightlife)", "icon": "🌴"},
                {"label": "South Goa — Serenity & Heritage", "value": "South Goa (heritage/relaxation)", "icon": "🏰"},
                {"label": "Balanced North & South Mix", "value": "Balanced mix across Goa", "icon": "⚖️"},
            ]
        },
        {
            "id": "travel_pace",
            "question": "What travel pace feels best for this trip?",
            "category": "pace",
            "options": [
                {"label": "Relaxed & Leisurely (2-3 spots/day)", "value": "slow", "icon": "🧘"},
                {"label": "Active & Exploring (4-5 stops/day)", "value": "moderate", "icon": "⚡"},
            ]
        },
        {
            "id": "gem_focus",
            "question": "How would you like to balance attractions and hidden gems?",
            "category": "travel_style",
            "options": [
                {"label": "Authentic Local Hidden Gems", "value": "niche", "icon": "💎"},
                {"label": "Curated 50/50 Balance", "value": "balanced", "icon": "✨"},
                {"label": "Iconic Must-See Sights", "value": "popular", "icon": "🏛️"},
            ]
        }
    ],
    "mumbai": [
        {
            "id": "mumbai_vibe",
            "question": "What experience are you looking for in Mumbai?",
            "category": "travel_style",
            "options": [
                {"label": "Colonial Heritage & South Bombay", "value": "cultural", "icon": "🏛️"},
                {"label": "Street Food, Cafes & Coastal Walks", "value": "foodie", "icon": "🍲"},
                {"label": "Hidden Art Enclaves & Bazaars", "value": "niche", "icon": "💎"},
            ]
        },
        {
            "id": "travel_pace",
            "question": "What travel pace suits your trip?",
            "category": "pace",
            "options": [
                {"label": "Relaxed (2-3 spots/day)", "value": "slow", "icon": "🧘"},
                {"label": "Moderate (4-5 spots/day)", "value": "moderate", "icon": "⚡"},
            ]
        }
    ],
    "pune": [
        {
            "id": "pune_vibe",
            "question": "What would you like to explore in Pune?",
            "category": "travel_style",
            "options": [
                {"label": "Maratha Forts & Historic Wadas", "value": "cultural", "icon": "🏰"},
                {"label": "Irani Cafes & Street Food", "value": "foodie", "icon": "☕"},
                {"label": "Scenic Hills & Hidden Green Spots", "value": "niche", "icon": "🌿"},
            ]
        },
        {
            "id": "travel_pace",
            "question": "What daily pace would you prefer?",
            "category": "pace",
            "options": [
                {"label": "Relaxed (2-3 spots/day)", "value": "slow", "icon": "🧘"},
                {"label": "Active (4-5 stops/day)", "value": "moderate", "icon": "⚡"},
            ]
        }
    ],
    "rajasthan": [
        {
            "id": "rajasthan_style",
            "question": "What is your primary focus for Rajasthan?",
            "category": "travel_style",
            "options": [
                {"label": "Royal Forts & Palaces", "value": "cultural", "icon": "👑"},
                {"label": "Stepwells & Desert Secrets", "value": "niche", "icon": "🏜️"},
                {"label": "Bazaars & Heritage Food", "value": "foodie", "icon": "🛍️"},
            ]
        },
        {
            "id": "travel_pace",
            "question": "What sightseeing pace would you prefer?",
            "category": "pace",
            "options": [
                {"label": "Relaxed (2-3 stops/day)", "value": "slow", "icon": "🧘"},
                {"label": "Moderate (4-5 stops/day)", "value": "moderate", "icon": "⚡"},
            ]
        }
    ],
    "lisbon": [
        {
            "id": "lisbon_vibe",
            "question": "What atmosphere are you most excited to experience in Lisbon?",
            "category": "travel_style",
            "options": [
                {"label": "Historic Castles & Miradouros", "value": "cultural", "icon": "🏰"},
                {"label": "Food, Pastéis & Fado Culture", "value": "foodie", "icon": "🍷"},
                {"label": "Secret Neighborhoods & Flea Markets", "value": "niche", "icon": "💎"},
            ]
        },
        {
            "id": "travel_pace",
            "question": "What daily pace suits your trip?",
            "category": "pace",
            "options": [
                {"label": "Relaxed Morning & Afternoon", "value": "slow", "icon": "☕"},
                {"label": "Comprehensive Day Exploration", "value": "moderate", "icon": "🚶"},
            ]
        }
    ]
}


def _get_generic_clarification_questions(destination: str) -> list[ClarificationQuestion]:
    """Fallback clarifying questions for any global destination."""
    raw_qs = [
        {
            "id": "travel_style",
            "question": f"What type of experience are you looking for in {destination}?",
            "category": "travel_style",
            "options": [
                {"label": "Curated Iconic Sights + Hidden Gems", "value": "balanced", "icon": "✨"},
                {"label": "Off-The-Beaten-Path Secrets", "value": "niche", "icon": "💎"},
                {"label": "Major World Landmarks", "value": "popular", "icon": "🏛️"},
                {"label": "Food, Cafes & Local Gastronomy", "value": "foodie", "icon": "🍲"},
            ]
        },
        {
            "id": "travel_pace",
            "question": "What is your preferred daily pace?",
            "category": "pace",
            "options": [
                {"label": "Relaxed (2-3 stops/day)", "value": "slow", "icon": "🧘"},
                {"label": "Moderate (4-5 stops/day)", "value": "moderate", "icon": "⚡"},
                {"label": "Packed (6+ stops/day)", "value": "fast", "icon": "🏃"},
            ]
        }
    ]
    return [
        ClarificationQuestion(
            id=q["id"],
            question=q["question"],
            category=q["category"],
            options=[ClarificationOption(**opt) for opt in q["options"]]
        )
        for q in raw_qs
    ]


# ── Slot extraction with LLM ────────────────────────────────────────────────
INTAKE_SYSTEM_PROMPT = """You are an expert travel intake agent. Convert the user's travel request into a structured JSON object.
Extract:
- destination: string (required, city/region/country name. Never return 'Unknown' if a city like Pune, Mumbai, Goa is mentioned)
- num_days: integer (1-14, default 3 if not specified)
- budget_usd: float or null
- niche_weight: float (0.0 to 1.0, default 0.5)
- travel_style: one of ["popular", "balanced", "niche", "cultural", "adventure", "foodie", "relaxed"]
- pace: one of ["slow", "moderate", "fast"]
- group_type: one of ["solo", "couple", "family", "friends"]
- interests: array of strings

Respond ONLY with valid JSON. No markdown, no explanation."""


async def _extract_with_llm(text: str) -> Optional[dict]:
    # 1. Try Gemini 3.5 Flash first (fastest, high rate limit)
    if GOOGLE_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-3.5-flash",
                google_api_key=GOOGLE_KEY,
                temperature=0.0,
            )
            messages = [
                {"role": "system", "content": INTAKE_SYSTEM_PROMPT},
                {"role": "user",   "content": text},
            ]
            response = await llm.ainvoke(messages)
            raw = response.content.strip()
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                if data.get("destination") and data["destination"].lower() != "unknown":
                    return data
        except Exception as e:
            print(f"[intake_agent] Gemini extraction failed: {e}")

    # 2. Try Groq (gpt-oss-20b)
    if GROQ_KEY:
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(
                model="openai/gpt-oss-20b",
                api_key=GROQ_KEY,
                temperature=0.0,
            )
            messages = [
                {"role": "system", "content": INTAKE_SYSTEM_PROMPT},
                {"role": "user",   "content": text},
            ]
            response = await llm.ainvoke(messages)
            raw = response.content.strip()
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                if data.get("destination") and data["destination"].lower() != "unknown":
                    return data
        except Exception as e:
            print(f"[intake_agent] Groq extraction failed: {e}")

    return None


def _extract_with_regex(text: str) -> dict:
    """Robust rule-based parser for city, duration, budget, style."""
    text_lower = text.lower().strip()

    # Destination parsing
    destination = "Unknown"
    for prep in ["in ", "to ", "for ", "around ", "visit ", "explore "]:
        if prep in text_lower:
            parts = text_lower.split(prep, 1)
            candidate = parts[1].split(",")[0].split()[0].strip(".,!?").title()
            if candidate and candidate.lower() not in ["a", "the", "my", "our", "some", "trip", "days", "standard", "preferences", "defaults"]:
                destination = candidate
                break

    # If destination is still Unknown, check if the first or last word is a known city/place
    if destination == "Unknown":
        words = [w.strip(".,!?") for w in text.split()]
        common_stops = {"3", "4", "5", "2", "1", "days", "day", "trip", "in", "to", "plan", "with", "submit", "preferences"}
        candidates = [w.title() for w in words if w.lower() not in common_stops and len(w) > 2]
        if candidates:
            destination = candidates[0]

    # Number of days
    num_days = 3
    day_match = re.search(r'(\d+)\s*(?:day|night)', text_lower)
    if day_match:
        num_days = int(day_match.group(1))
    elif "weekend" in text_lower:
        num_days = 2
    elif "week" in text_lower:
        num_days = 7

    # Budget
    budget_usd = None
    budget_match = re.search(r'[\$€£](\d[\d,]*)|\b(\d[\d,]*)\s*(?:usd|dollars|euro|inr|rs|bucks|rupees)\b', text_lower)
    if budget_match:
        raw_val = budget_match.group(1) or budget_match.group(2)
        try:
            budget_usd = float(raw_val.replace(",", ""))
        except ValueError:
            pass

    # Travel style & Niche weight
    travel_style = "balanced"
    niche_weight = 0.5
    if any(w in text_lower for w in ["hidden gem", "offbeat", "secret", "local", "niche", "authentic"]):
        travel_style = "niche"
        niche_weight = 0.75
    elif any(w in text_lower for w in ["iconic", "must see", "tourist", "famous", "landmark"]):
        travel_style = "popular"
        niche_weight = 0.2
    elif any(w in text_lower for w in ["food", "foodie", "eat", "cafe", "restaurant"]):
        travel_style = "foodie"
    elif any(w in text_lower for w in ["culture", "history", "museum", "temple", "palace", "wada", "fort"]):
        travel_style = "cultural"

    # Group type
    group_type = "solo"
    if "couple" in text_lower or "honeymoon" in text_lower or "partner" in text_lower:
        group_type = "couple"
    elif "family" in text_lower or "kids" in text_lower:
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
    Intake LangGraph node:
    1. Extracts slots from user message (with fallback to previous turn or explicit state).
    2. Incorporates any user-selected clarification answers.
    3. If prompt is minimal and force_plan is False -> asks clarifying questions with chips.
    4. Otherwise -> proceeds to Ranker & Planner.
    """
    events = list(state.get("events", []))
    messages = state["messages"]
    last_user_msg = messages[-1].content if messages else "Trip to Goa"

    force_plan = state.get("force_plan", False)
    answers = state.get("clarification_answers") or {}
    explicit_dest = state.get("destination")
    explicit_days = state.get("num_days")

    events.append(AgentEvent(
        event_type="agent_start",
        agent="intake_agent",
        message="Analyzing your destination, duration, and travel preferences...",
    ))

    # Try LLM extraction first, fall back to regex
    extracted = await _extract_with_llm(last_user_msg)
    if not extracted:
        extracted = _extract_with_regex(last_user_msg)

    # If explicit destination/days passed in state, prioritize them
    if explicit_dest and explicit_dest.lower() != "unknown":
        extracted["destination"] = explicit_dest
    if explicit_days:
        extracted["num_days"] = explicit_days

    # If destination is still Unknown, check if previous trip_request has it
    if extracted.get("destination") == "Unknown" and state.get("trip_request"):
        prev_trip = state["trip_request"]
        if prev_trip.destination and prev_trip.destination != "Unknown":
            extracted["destination"] = prev_trip.destination
            extracted["num_days"] = prev_trip.num_days

    # Merge explicit clarification answers if user clicked chips
    if answers:
        if "travel_style" in answers:
            extracted["travel_style"] = answers["travel_style"]
            if answers["travel_style"] == "niche":
                extracted["niche_weight"] = 0.8
            elif answers["travel_style"] == "popular":
                extracted["niche_weight"] = 0.2
        if "pace" in answers:
            extracted["pace"] = answers["pace"]
        if "region_vibe" in answers:
            extracted["region_preference"] = answers["region_vibe"]

    trip_request = _dict_to_trip_request(extracted, raw_message=last_user_msg)
    if "region_preference" in extracted:
        trip_request.region_preference = extracted["region_preference"]

    # ── Check if prompt is underspecified ─────────────────────────────────
    is_brief_prompt = len(last_user_msg.split()) <= 7 and not answers and trip_request.budget_usd is None
    needs_clarification = is_brief_prompt and not force_plan

    if needs_clarification and trip_request.destination != "Unknown":
        dest_lower = trip_request.destination.lower()
        matched_key = next((k for k in DESTINATION_QUESTIONS if k in dest_lower), None)

        if matched_key:
            raw_qs = DESTINATION_QUESTIONS[matched_key]
            questions = [
                ClarificationQuestion(
                    id=q["id"],
                    question=q["question"],
                    category=q["category"],
                    options=[ClarificationOption(**opt) for opt in q["options"]]
                )
                for q in raw_qs
            ]
        else:
            questions = _get_generic_clarification_questions(trip_request.destination)

        events.append(AgentEvent(
            event_type="clarification_needed",
            agent="intake_agent",
            message=f"I've got {trip_request.num_days} days in {trip_request.destination} noted! To make this itinerary truly personal, tell me a bit about your travel style below (or click 'Plan with defaults now' to start immediately).",
            data={
                "questions": [q.model_dump() for q in questions],
                "destination": trip_request.destination,
                "num_days": trip_request.num_days,
            }
        ))

        return {
            "trip_request": trip_request,
            "destination": trip_request.destination,
            "num_days": trip_request.num_days,
            "needs_clarification": True,
            "clarification_questions": questions,
            "events": events,
        }

    # If complete or forced, proceed to planning
    events.append(AgentEvent(
        event_type="agent_step",
        agent="intake_agent",
        message=f"Trip preferences confirmed: {trip_request.num_days} days in {trip_request.destination} ({trip_request.travel_style.value} style, {trip_request.pace.value} pace).",
    ))

    return {
        "trip_request": trip_request,
        "destination": trip_request.destination,
        "num_days": trip_request.num_days,
        "needs_clarification": False,
        "clarification_questions": [],
        "events": events,
    }
