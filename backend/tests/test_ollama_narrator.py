"""
Unit tests for Local Ollama Narrator (Phase 5).
Verifies:
1. Model discovery and availability checks (handling both online and offline states)
2. Stop narration generation with proper prompt formatting
3. Batch narration generation across multiple stops
4. Graceful fallback on network timeout or server absence
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from app.models.schemas import Stop
from app.tools.ollama_narrator import (
    get_available_ollama_model,
    is_ollama_available,
    generate_stop_narration,
    generate_stop_narrations_batch,
    OLLAMA_HOST,
)


@pytest.mark.anyio
async def test_get_available_ollama_model_success():
    """Test model detection when Ollama is running with preferred models."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [
            {"name": "llama3.2:3b"},
            {"name": "travel-narrator:latest"},
        ]
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    model = await get_available_ollama_model(client=mock_client)
    assert model in ["travel-narrator", "travel-narrator:latest", "llama3.2:3b"]


@pytest.mark.anyio
async def test_get_available_ollama_model_offline():
    """Test offline behavior when Ollama is not running."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

    model = await get_available_ollama_model(client=mock_client)
    assert model is None


@pytest.mark.anyio
async def test_generate_stop_narration_success():
    """Test successful narration generation."""
    sample_text = "Wander pastel-washed Portuguese villas where morning light filters through bougainvillea."

    mock_generate_resp = MagicMock()
    mock_generate_resp.status_code = 200
    mock_generate_resp.json.return_value = {"response": sample_text}

    with patch("httpx.AsyncClient.get") as mock_get, patch("httpx.AsyncClient.post") as mock_post:
        mock_tags_resp = MagicMock()
        mock_tags_resp.status_code = 200
        mock_tags_resp.json.return_value = {"models": [{"name": "travel-narrator:latest"}]}
        mock_get.return_value = mock_tags_resp

        mock_post.return_value = mock_generate_resp

        narration = await generate_stop_narration(
            place_name="Fontainhas",
            category="cultural",
            destination="Goa",
            context="Pastel villas and Latin quarter",
        )

        assert narration is not None
        assert "villas" in narration.lower()
        assert len(narration) > 15


@pytest.mark.anyio
async def test_generate_stop_narration_empty_name():
    """Test that empty or trivial place names return None immediately."""
    narration = await generate_stop_narration(
        place_name="",
        category="cultural",
        destination="Goa",
    )
    assert narration is None


@pytest.mark.anyio
async def test_generate_stop_narrations_batch():
    """Test batch narration generation across multiple stops."""
    stops = [
        Stop(
            id="stop-1",
            name="Fontainhas",
            category="cultural",
            description="Historic Portuguese quarter",
            narration="Default",
            lat=15.5,
            lon=73.8,
            duration_minutes=60,
            estimated_cost_usd=5.0,
            photo_urls=[],
            source="opentripmap",
        ),
        Stop(
            id="stop-2",
            name="Cabo de Rama",
            category="viewpoint",
            description="Clifftop fort over ocean",
            narration="Default",
            lat=15.05,
            lon=73.9,
            duration_minutes=60,
            estimated_cost_usd=0.0,
            photo_urls=[],
            source="opentripmap",
        ),
    ]

    with patch("app.tools.ollama_narrator.get_available_ollama_model", return_value="travel-narrator"), \
         patch("app.tools.ollama_narrator.generate_stop_narration", side_effect=[
             "Pastel villas glow softly in the coastal morning light.",
             "Dramatic sea cliffs overlook crashing turquoise ocean waves."
         ]):
        results = await generate_stop_narrations_batch(stops, "Goa")
        assert len(results) == 2
        assert results[0] is not None
        assert "villas" in results[0]
        assert results[1] is not None
        assert "cliffs" in results[1]
