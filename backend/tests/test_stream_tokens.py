"""
Unit tests for Phase 12A:
- Word-by-word LLM Chat Streaming (text_token SSE events)
- Pre-stream typing indicator support
- Reconstructed text verification & backward compatibility
"""
import json
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import AgentEvent, TripRequest, DayPlan, Stop, Itinerary


def test_stream_word_by_word_text_tokens():
    """Verify that assistant_reply is split into word-by-word text_token SSE events."""
    mock_reply = "Welcome to Goa! Here is a wonderful 3-day beach escape."
    mock_graph_result = {
        "events": [
            AgentEvent(event_type="agent_step", agent="intake_agent", message="Routing complete.")
        ],
        "assistant_reply": mock_reply,
        "itinerary": None,
    }

    client = TestClient(app)

    with patch("app.main.travel_graph.ainvoke", new=AsyncMock(return_value=mock_graph_result)):
        response = client.post(
            "/plan/stream",
            json={"message": "tell me about Goa", "session_id": "test-session-12a"},
        )

        assert response.status_code == 200
        content = response.text

        # Collect chunks and events
        lines = content.split("\n")
        chunks = []
        has_assistant_message = False
        has_done_event = False

        for line in lines:
            if line.startswith("data: "):
                data_str = line[6:].strip()
                if not data_str:
                    continue
                try:
                    payload = json.loads(data_str)
                    if payload.get("event_type") == "text_token":
                        chunks.append(payload["chunk"])
                    elif payload.get("event_type") == "assistant_message":
                        has_assistant_message = True
                        assert payload["message"] == mock_reply
                    elif payload.get("event_type") == "done":
                        has_done_event = True
                except json.JSONDecodeError:
                    pass

        # Verify word-by-word streaming occurred
        assert len(chunks) > 1, f"Expected multiple word chunks, got {len(chunks)}"
        reconstructed = "".join(chunks)
        assert reconstructed == mock_reply
        assert has_assistant_message is True
        assert has_done_event is True
