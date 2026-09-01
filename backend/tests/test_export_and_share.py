"""
Unit tests for PDF Export and Itinerary Sharing (Phase 6).
Verifies:
1. HTML template generation with complete metadata, weather notes, and atmospheric narrations
2. PDF byte generation via Playwright / HTML fallback
3. GET /export/pdf/{itinerary_id} endpoint (200 success & 404 handling)
4. POST /export/pdf direct endpoint
5. GET /share/{slug_or_id} public trip retrieval endpoint
"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.schemas import Itinerary, TripRequest, DayPlan, Stop
from app.db.history_store import save_itinerary
from app.tools.pdf_generator import generate_itinerary_html, generate_itinerary_pdf


def _create_sample_itinerary(itinerary_id: str = "itin-share-test-123") -> Itinerary:
    stops_day1 = [
        Stop(
            id="stop-1",
            name="Fontainhas Latin Quarter",
            category="cultural",
            description="Historic Portuguese quarter with colorful villas.",
            narration="Wander pastel-washed Portuguese villas glowing softly under bougainvillea.",
            lat=15.4989,
            lon=73.8322,
            duration_minutes=90,
            estimated_cost_usd=5.0,
            photo_urls=["https://example.com/fontainhas.jpg"],
            source="opentripmap",
            is_niche=True,
        ),
        Stop(
            id="stop-2",
            name="Miramar Beach Promenade",
            category="viewpoint",
            description="Scenic coastal promenade along the Arabian Sea.",
            narration="Golden sunset breezes ripple across the tranquil coastal sands.",
            lat=15.4820,
            lon=73.8070,
            duration_minutes=60,
            estimated_cost_usd=0.0,
            photo_urls=["https://example.com/miramar.jpg"],
            source="opentripmap",
        ),
    ]

    day1 = DayPlan(
        day_number=1,
        theme="Colonial Panjim & Coastal Sunsets",
        stops=stops_day1,
        day_cost_estimate_usd=5.0,
        weather_note="Sunny, 29°C",
    )

    return Itinerary(
        id=itinerary_id,
        trip_request=TripRequest(
            destination="Goa",
            num_days=1,
            travel_style="balanced",
            pace="moderate",
        ),
        days=[day1],
        total_cost_estimate_usd=5.0,
        cover_image_url="https://example.com/goa-banner.jpg",
    )


def test_generate_itinerary_html():
    """Verify HTML template structure and content injection."""
    itinerary = _create_sample_itinerary()
    html = generate_itinerary_html(itinerary)

    assert "WanderAI" in html
    assert "Goa" in html
    assert "Fontainhas Latin Quarter" in html
    assert "Colonial Panjim & Coastal Sunsets" in html
    assert "Sunny, 29°C" in html
    assert "HIDDEN GEM" in html
    assert "pastel-washed" in html


@pytest.mark.anyio
async def test_generate_itinerary_pdf_bytes():
    """Verify that PDF generation produces valid non-empty byte stream."""
    itinerary = _create_sample_itinerary()
    pdf_bytes = await generate_itinerary_pdf(itinerary)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500


@pytest.mark.anyio
async def test_export_pdf_by_id_success():
    """Test GET /export/pdf/{id} returns 200 with PDF content-type."""
    itinerary = _create_sample_itinerary("itin-export-id-456")
    save_itinerary(itinerary)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/export/pdf/{itinerary.id}")
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        assert "attachment" in response.headers.get("content-disposition", "")
        assert len(response.content) > 500


@pytest.mark.anyio
async def test_export_pdf_by_id_404():
    """Test GET /export/pdf/{invalid_id} returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/export/pdf/non-existent-itin-id-999")
        assert response.status_code == 404
        assert "not found" in response.json().get("detail", "").lower()


@pytest.mark.anyio
async def test_export_pdf_direct_post():
    """Test POST /export/pdf returns 200 with PDF content-type."""
    itinerary = _create_sample_itinerary("itin-direct-post-789")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/export/pdf", json=itinerary.model_dump())
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        assert "attachment" in response.headers.get("content-disposition", "")
        assert len(response.content) > 500


@pytest.mark.anyio
async def test_get_shared_trip_success():
    """Test GET /share/{slug_or_id} retrieves saved itinerary."""
    itinerary = _create_sample_itinerary("itin-share-success-321")
    save_itinerary(itinerary)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/share/{itinerary.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == itinerary.id
        assert data["trip_request"]["destination"] == "Goa"
        assert len(data["days"]) == 1


@pytest.mark.anyio
async def test_get_shared_trip_404():
    """Test GET /share/{invalid_id} returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/share/unknown-fake-slug-000")
        assert response.status_code == 404
        assert "not found" in response.json().get("detail", "").lower()
