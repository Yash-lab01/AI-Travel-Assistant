"""
Unit tests for Trip History Store (Phase 4f).
Verifies:
1. save_itinerary saves metadata and full JSON
2. get_all_histories retrieves ordered summary list
3. get_itinerary_by_id loads deserialized full Itinerary object
4. delete_itinerary removes record correctly
5. Max history pruning limit
"""
import pytest
import os
import tempfile
import uuid

from app.models.schemas import TripRequest, Stop, DayPlan, Itinerary
from app.db.history_store import (
    init_db,
    save_itinerary,
    get_all_histories,
    get_itinerary_by_id,
    delete_itinerary,
)


@pytest.fixture
def temp_db_path():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    init_db(path)
    yield path
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


def _create_sample_itinerary(dest: str = "Goa", days_count: int = 2) -> Itinerary:
    stops = [
        Stop(
            id=str(uuid.uuid4()),
            name=f"Spot in {dest}",
            category="attraction",
            description=f"Iconic attraction in {dest}.",
            narration=f"A must-see landmark in {dest}.",
            lat=15.5,
            lon=73.8,
            duration_minutes=60,
            estimated_cost_usd=10.0,
            photo_urls=["https://example.com/photo.jpg"],
            source="opentripmap",
        )
    ]
    days = [
        DayPlan(
            day_number=i + 1,
            theme=f"Day {i + 1} Theme in {dest}",
            stops=stops,
            day_cost_estimate_usd=10.0,
            cover_image_url="https://example.com/day_cover.jpg",
        )
        for i in range(days_count)
    ]
    trip_req = TripRequest(
        destination=dest,
        num_days=days_count,
        travel_style="balanced",
        pace="moderate",
        interests=["beaches", "culture"],
    )
    return Itinerary(
        id=str(uuid.uuid4()),
        trip_request=trip_req,
        days=days,
        total_cost_estimate_usd=days_count * 10.0,
        cover_image_url="https://example.com/trip_cover.jpg",
    )


def test_save_and_get_all_histories(temp_db_path):
    itin1 = _create_sample_itinerary(dest="Goa", days_count=3)
    itin2 = _create_sample_itinerary(dest="Mumbai", days_count=2)

    res1 = save_itinerary(itin1, db_path=temp_db_path)
    res2 = save_itinerary(itin2, db_path=temp_db_path)

    assert res1["destination"] == "Goa"
    assert res1["num_days"] == 3
    assert res2["destination"] == "Mumbai"

    histories = get_all_histories(limit=10, db_path=temp_db_path)
    assert len(histories) == 2
    destinations = [h["destination"] for h in histories]
    assert "Mumbai" in destinations
    assert "Goa" in destinations


def test_get_itinerary_by_id(temp_db_path):
    itin = _create_sample_itinerary(dest="Rajasthan", days_count=4)
    save_itinerary(itin, db_path=temp_db_path)

    loaded = get_itinerary_by_id(itin.id, db_path=temp_db_path)
    assert loaded is not None
    assert loaded.id == itin.id
    assert loaded.trip_request.destination == "Rajasthan"
    assert len(loaded.days) == 4
    assert loaded.days[0].stops[0].name == "Spot in Rajasthan"


def test_delete_itinerary(temp_db_path):
    itin = _create_sample_itinerary(dest="Tokyo", days_count=5)
    save_itinerary(itin, db_path=temp_db_path)

    assert get_itinerary_by_id(itin.id, db_path=temp_db_path) is not None

    deleted = delete_itinerary(itin.id, db_path=temp_db_path)
    assert deleted is True

    # Confirm it no longer exists
    assert get_itinerary_by_id(itin.id, db_path=temp_db_path) is None

    # Deleting non-existent returns False
    assert delete_itinerary("non-existent-id", db_path=temp_db_path) is False


def test_history_limit_pruning(temp_db_path):
    """Test that records exceeding max_history_limit are pruned."""
    itins = [_create_sample_itinerary(dest=f"City {i}", days_count=1) for i in range(7)]
    for itin in itins:
        save_itinerary(itin, db_path=temp_db_path, max_history_limit=4)

    all_saved = get_all_histories(limit=10, db_path=temp_db_path)
    assert len(all_saved) == 4
