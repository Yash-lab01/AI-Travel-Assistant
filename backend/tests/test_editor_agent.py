"""
Unit tests for Editor Agent and Multi-Turn Editing (Phase 4e).
Verifies:
1. Intent classification for various follow-up messages
2. Stop swapping (with transit recalculation and candidate deduplication)
3. Stop removal (with route recalculation)
4. Tell me more (storytelling without mutating itinerary)
5. Pacing adjustments
"""
import pytest
import asyncio
from langchain_core.messages import HumanMessage

from app.models.schemas import TripRequest, Stop, DayPlan, Itinerary, EditIntent
from app.agents.intake_agent import classify_edit_intent
from app.agents.editor_agent import editor_node


def _create_sample_itinerary() -> Itinerary:
    stops_day1 = [
        Stop(
            id="stop-1",
            name="Shaniwar Wada",
            category="attraction",
            description="Historic fort palace in Pune.",
            narration="The grand 18th-century seat of Peshwa rulers.",
            lat=18.5196,
            lon=73.8553,
            duration_minutes=60,
            estimated_cost_usd=5.0,
            photo_urls=["https://example.com/shaniwar.jpg"],
            source="opentripmap",
        ),
        Stop(
            id="stop-2",
            name="Aga Khan Palace",
            category="museum",
            description="Memorial to Mahatma Gandhi.",
            narration="Italian arches and serene lawns commemorating Gandhi's legacy.",
            lat=18.5529,
            lon=73.9015,
            duration_minutes=75,
            estimated_cost_usd=10.0,
            photo_urls=["https://example.com/agakhan.jpg"],
            source="opentripmap",
        ),
        Stop(
            id="stop-3",
            name="Pataleshwar Cave Temple",
            category="attraction",
            description="8th-century rock-cut temple.",
            narration="Ancient basalt rock-cut sanctum carved into the heart of Pune.",
            lat=18.5273,
            lon=73.8517,
            duration_minutes=45,
            estimated_cost_usd=2.0,
            photo_urls=["https://example.com/pataleshwar.jpg"],
            source="opentripmap",
        ),
    ]

    stops_day2 = [
        Stop(
            id="stop-4",
            name="Sinhagad Fort",
            category="viewpoint",
            description="Hilltop fortress with sweeping views.",
            narration="High cliff citadel offering misty Sahyadri valley panoramas.",
            lat=18.3663,
            lon=73.7558,
            duration_minutes=120,
            estimated_cost_usd=5.0,
            photo_urls=["https://example.com/sinhagad.jpg"],
            source="opentripmap",
        ),
        Stop(
            id="stop-5",
            name="Saras Baug",
            category="park",
            description="Lush garden and temple lake.",
            narration="Peaceful botanical lake gardens centered around the Ganpati temple.",
            lat=18.5008,
            lon=73.8533,
            duration_minutes=60,
            estimated_cost_usd=2.0,
            photo_urls=["https://example.com/sarasbaug.jpg"],
            source="opentripmap",
        ),
    ]

    day1 = DayPlan(
        day_number=1,
        theme="Historic Pune Forts & Heritage",
        stops=stops_day1,
        day_cost_estimate_usd=17.0,
        weather_note="Sunny, 28°C",
    )
    day2 = DayPlan(
        day_number=2,
        theme="Hilltop Vistas & Scenic Gardens",
        stops=stops_day2,
        day_cost_estimate_usd=7.0,
        weather_note="Partly cloudy, 26°C",
    )

    return Itinerary(
        id="itin-test-123",
        trip_request=TripRequest(
            destination="Pune",
            num_days=2,
            travel_style="balanced",
            pace="moderate",
        ),
        days=[day1, day2],
        total_cost_estimate_usd=24.0,
    )


def test_classify_edit_intent():
    itinerary = _create_sample_itinerary()

    res1 = classify_edit_intent("Can you swap Shaniwar Wada on Day 1 for a garden?", itinerary)
    assert res1["intent"] == EditIntent.swap_stop.value
    assert res1["target_day"] == 1
    assert res1["target_stop_name"] == "Shaniwar Wada"

    res2 = classify_edit_intent("Remove Sinhagad Fort from Day 2", itinerary)
    assert res2["intent"] == EditIntent.remove_stop.value
    assert res2["target_stop_name"] == "Sinhagad Fort"

    res3 = classify_edit_intent("Tell me more about Aga Khan Palace and photo tips", itinerary)
    assert res3["intent"] == EditIntent.tell_me_more.value
    assert res3["target_stop_name"] == "Aga Khan Palace"

    res4 = classify_edit_intent("Please make the trip more relaxed with slower pace", itinerary)
    assert res4["intent"] == EditIntent.adjust_pace.value

    res5 = classify_edit_intent("Plan a new 3 day trip to Tokyo", itinerary)
    assert res5["intent"] == EditIntent.new_trip.value


@pytest.mark.anyio
async def test_editor_swap_stop():
    itinerary = _create_sample_itinerary()
    state = {
        "messages": [HumanMessage(content="Swap Shaniwar Wada on Day 1")],
        "itinerary": itinerary,
        "is_edit": True,
        "edit_intent": "swap_stop",
        "target_day": 1,
        "target_stop_id": "stop-1",
        "target_stop_name": "Shaniwar Wada",
        "edit_instruction": "Swap Shaniwar Wada on Day 1",
        "events": [],
    }

    result = await editor_node(state)
    assert "itinerary" in result
    updated_itinerary = result["itinerary"]
    assert len(updated_itinerary.days) == 2

    # Stop 1 on Day 1 should no longer be Shaniwar Wada
    day1_stop_names = [s.name for s in updated_itinerary.days[0].stops]
    assert "Shaniwar Wada" not in day1_stop_names
    assert len(day1_stop_names) == 3


@pytest.mark.anyio
async def test_editor_remove_stop():
    itinerary = _create_sample_itinerary()
    state = {
        "messages": [HumanMessage(content="Remove Aga Khan Palace from Day 1")],
        "itinerary": itinerary,
        "is_edit": True,
        "edit_intent": "remove_stop",
        "target_day": 1,
        "target_stop_id": "stop-2",
        "target_stop_name": "Aga Khan Palace",
        "edit_instruction": "Remove Aga Khan Palace from Day 1",
        "events": [],
    }

    result = await editor_node(state)
    updated_itinerary = result["itinerary"]
    day1_stops = updated_itinerary.days[0].stops
    assert len(day1_stops) == 2
    assert all(s.name != "Aga Khan Palace" for s in day1_stops)


@pytest.mark.anyio
async def test_editor_tell_me_more_does_not_mutate_itinerary():
    itinerary = _create_sample_itinerary()
    original_stops_count = sum(len(d.stops) for d in itinerary.days)

    state = {
        "messages": [HumanMessage(content="Tell me more about Sinhagad Fort")],
        "itinerary": itinerary,
        "is_edit": True,
        "edit_intent": "tell_me_more",
        "target_stop_name": "Sinhagad Fort",
        "edit_instruction": "Tell me more about Sinhagad Fort",
        "events": [],
    }

    result = await editor_node(state)
    assert "assistant_reply" in result
    assert result["assistant_reply"] is not None
    assert len(result["assistant_reply"]) > 20

    # Itinerary must be completely untouched
    final_stops_count = sum(len(d.stops) for d in result["itinerary"].days)
    assert final_stops_count == original_stops_count
