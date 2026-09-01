"""
Phase 7 Unit Test Suite
Tests iCalendar (.ics) export, stop reordering, user feedback loop, and smart packing list generator.
"""
import pytest
from fastapi.testclient import TestClient
import os
import json

from app.main import app
from app.models.schemas import Itinerary, DayPlan, Stop, TripRequest, StopReorderRequest, StopFeedbackRequest
from app.tools.ical_generator import generate_itinerary_ical
from app.tools.packing_list_generator import generate_smart_packing_list
from app.db.history_store import save_itinerary
from app.db.feedback_store import record_stop_feedback, JSONL_FEEDBACK_PATH

client = TestClient(app)


@pytest.fixture
def sample_itinerary() -> Itinerary:
    return Itinerary(
        id="phase7-test-trip-12345",
        trip_request=TripRequest(
            destination="Lisbon, Portugal",
            num_days=2,
            travel_style="balanced",
            pace="moderate",
            interests=["culture", "food"],
        ),
        days=[
            DayPlan(
                day_number=1,
                theme="Historic Alfama & Castles",
                date="2026-09-10",
                weather_note="Sunny 24°C, 0% rain",
                stops=[
                    Stop(
                        id="stop-1",
                        name="São Jorge Castle",
                        category="attraction",
                        description="Moorish castle overlooking Lisbon.",
                        narration="Ancient stone fortifications with panoramic views of the Tagus river.",
                        lat=38.7139,
                        lon=-9.1335,
                        duration_minutes=90,
                        estimated_cost_usd=15.0,
                        travel_time_from_prev_minutes=0,
                        is_niche=False,
                    ),
                    Stop(
                        id="stop-2",
                        name="Miradouro de Santa Luzia",
                        category="viewpoint",
                        description="Bougainvillea-covered scenic viewpoint.",
                        narration="Sunlit azulejo tiles overlooking the terracotta rooftops of Alfama.",
                        lat=38.7116,
                        lon=-9.1303,
                        duration_minutes=45,
                        estimated_cost_usd=0.0,
                        travel_time_from_prev_minutes=8,
                        is_niche=True,
                    ),
                    Stop(
                        id="stop-3",
                        name="Pastéis de Belém",
                        category="cafe",
                        description="Historic bakery serving custard tarts.",
                        narration="Warm crispy puff pastry with cinnamon custard.",
                        lat=38.6975,
                        lon=-9.2032,
                        duration_minutes=40,
                        estimated_cost_usd=6.0,
                        travel_time_from_prev_minutes=25,
                        is_niche=False,
                    ),
                ],
            ),
            DayPlan(
                day_number=2,
                theme="Belem & Coastal Heritage",
                date="2026-09-11",
                weather_note="Partly Cloudy 22°C",
                stops=[
                    Stop(
                        id="stop-4",
                        name="Belém Tower",
                        category="attraction",
                        description="Fortified tower on the Tagus estuary.",
                        narration="Manueline stone watchtower welcoming seafaring voyagers.",
                        lat=38.6916,
                        lon=-9.2160,
                        duration_minutes=60,
                        estimated_cost_usd=10.0,
                        travel_time_from_prev_minutes=0,
                        is_niche=False,
                    )
                ],
            ),
        ],
        total_cost_estimate_usd=31.0,
    )


def test_ical_generator_format(sample_itinerary: Itinerary):
    """Verify that generate_itinerary_ical creates valid RFC 5545 format."""
    ical_str = generate_itinerary_ical(sample_itinerary)
    
    assert "BEGIN:VCALENDAR" in ical_str
    assert "END:VCALENDAR" in ical_str
    assert "VERSION:2.0" in ical_str
    assert "PRODID:-//WanderAI//Travel Planner//EN" in ical_str
    assert "BEGIN:VEVENT" in ical_str
    assert "SUMMARY:São Jorge Castle" in ical_str
    assert "SUMMARY:Miradouro de Santa Luzia" in ical_str
    assert "GEO:38.713900;-9.133500" in ical_str
    assert "STATUS:CONFIRMED" in ical_str


def test_ical_export_endpoints(sample_itinerary: Itinerary):
    """Test both GET by ID and POST direct .ics calendar export routes."""
    # 1. Save trip first
    save_itinerary(sample_itinerary)

    # 2. Test GET /export/ical/{id}
    res = client.get(f"/export/ical/{sample_itinerary.id}")
    assert res.status_code == 200
    assert "text/calendar" in res.headers["content-type"]
    assert "BEGIN:VCALENDAR" in res.text
    assert "Pastéis de Belém" in res.text

    # 3. Test POST /export/ical direct
    res_post = client.post("/export/ical", json=sample_itinerary.model_dump())
    assert res_post.status_code == 200
    assert "text/calendar" in res_post.headers["content-type"]
    assert "Belém Tower" in res_post.text


def test_reorder_stops_endpoint(sample_itinerary: Itinerary):
    """Test reordering stops on Day 1 and verify transit recalculation."""
    save_itinerary(sample_itinerary)

    # Reorder: Stop-3 first, then Stop-1, then Stop-2
    payload = {
        "day_number": 1,
        "stop_ids": ["stop-3", "stop-1", "stop-2"],
    }

    res = client.post(f"/plan/{sample_itinerary.id}/reorder", json=payload)
    assert res.status_code == 200
    data = res.json()
    
    day1_stops = data["days"][0]["stops"]
    assert len(day1_stops) == 3
    assert day1_stops[0]["id"] == "stop-3"
    assert day1_stops[0]["travel_time_from_prev_minutes"] == 0
    assert day1_stops[1]["id"] == "stop-1"
    assert day1_stops[1]["travel_time_from_prev_minutes"] > 0
    assert day1_stops[2]["id"] == "stop-2"


def test_submit_stop_feedback():
    """Test submitting 👍 / 👎 stop feedback."""
    feedback = StopFeedbackRequest(
        itinerary_id="test-trip-123",
        stop_id="test-stop-101",
        stop_name="Historic Miradouro",
        destination="Lisbon, Portugal",
        rating=1,
        category="viewpoint",
        is_niche=True,
    )

    res = client.post("/feedback", json=feedback.model_dump())
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["rating"] == 1
    assert data["stop_name"] == "Historic Miradouro"


import asyncio

def test_smart_packing_list(sample_itinerary: Itinerary):
    """Test smart packing list generator returns categorized essentials."""
    res = asyncio.run(generate_smart_packing_list(sample_itinerary))
    
    assert res.destination == "Lisbon, Portugal"
    assert len(res.categories) >= 3
    category_names = [c.name for c in res.categories]
    assert any("Clothing" in n for n in category_names)
    assert any("Weather" in n or "Toiletries" in n for n in category_names)
    assert any("Tech" in n or "Power" in n for n in category_names)

