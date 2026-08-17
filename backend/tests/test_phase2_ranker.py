"""
Unit & Integration Tests for Phase 2:
- Hidden gem scoring with VADER sentiment
- Niche spot extraction & discovery
- Ranker Agent blending logic
- Full LangGraph async execution
"""
import pytest
import asyncio
from langchain_core.messages import HumanMessage

from app.models.schemas import (
    TripRequest, Stop, NicheScore, TravelStyle, TravelPace
)
from app.scoring.hidden_gem_score import compute_hidden_gem_score
from app.tools.niche_scraper import discover_niche_spots
from app.agents.ranker_agent import ranker_node
from app.graph.travel_graph import travel_graph


def test_hidden_gem_scoring_logic():
    """Verify log-normalized scoring gives high score to niche gems and low to tourist traps."""
    # Niche gem: 15 mentions, +0.8 sentiment, 2 sources, 250 Google reviews
    niche_score = compute_hidden_gem_score(
        mention_count=15,
        avg_sentiment=0.8,
        source_types=["reddit", "tavily_blog"],
        google_review_count=250,
        max_review_count_in_batch=10_000,
    )
    assert niche_score >= 0.45, f"Expected high score for niche gem, got {niche_score}"

    # Mainstream tourist trap: 2 mentions, neutral sentiment, 1 source, 25,000 reviews
    tourist_trap_score = compute_hidden_gem_score(
        mention_count=2,
        avg_sentiment=0.1,
        source_types=["reddit"],
        google_review_count=25_000,
        max_review_count_in_batch=10_000,
    )
    assert tourist_trap_score <= 0.25, f"Expected low score for tourist trap, got {tourist_trap_score}"


def test_discover_niche_spots_lisbon():
    """Verify niche scraper extracts Lisbon spots with valid coordinates and niche scores."""
    async def run():
        spots = await discover_niche_spots("Lisbon")
        assert len(spots) >= 2, f"Expected at least 2 niche spots, got {len(spots)}"

        for s in spots:
            assert s.is_niche is True
            assert s.niche_score is not None
            assert 0.0 <= s.niche_score.hidden_gem_score <= 1.0
            assert s.lat != 0.0 and s.lon != 0.0

        # At least one spot has a solid positive gem score
        high_scorers = [s for s in spots if s.niche_score.hidden_gem_score > 0.15]
        assert len(high_scorers) >= 1, "Expected at least one high-scoring niche gem"

    asyncio.run(run())


def test_ranker_node_blending():
    """Verify ranker blends popular sights and niche spots according to niche_weight."""
    async def run():
        state = {
            "messages": [HumanMessage(content="3 days in Lisbon, hidden gems")],
            "trip_request": TripRequest(
                destination="Lisbon",
                num_days=3,
                niche_weight=0.75,
                travel_style=TravelStyle.balanced,
                pace=TravelPace.moderate,
            ),
            "popular_stops_raw": [],
            "niche_spots_raw": [],
            "ranked_stops": [],
            "itinerary": None,
            "events": [],
            "session_id": "test-session-ranker",
            "is_edit": False,
            "edit_instruction": None,
        }

        result = await ranker_node(state)
        ranked = result.get("ranked_stops", [])
        assert len(ranked) >= 6, f"Expected at least 6 ranked stops for 3 days, got {len(ranked)}"

        niche_stops = [s for s in ranked if s.is_niche]
        assert len(niche_stops) >= 2, f"Expected at least 2 niche stops with niche_weight=0.75, got {len(niche_stops)}"

    asyncio.run(run())


def test_full_phase2_langgraph_pipeline():
    """Verify end-to-end LangGraph execution with intake -> ranker -> planner."""
    async def run():
        state = {
            "messages": [HumanMessage(content="3 days in Lisbon, hidden gems, budget 800")],
            "trip_request": None,
            "popular_stops_raw": [],
            "niche_spots_raw": [],
            "ranked_stops": [],
            "itinerary": None,
            "events": [],
            "session_id": "test-e2e-phase2",
            "is_edit": False,
            "edit_instruction": None,
        }
        config = {"configurable": {"thread_id": "test-e2e-phase2"}}

        result = await travel_graph.ainvoke(state, config)
        itinerary = result.get("itinerary")

        assert itinerary is not None
        assert itinerary.trip_request.destination.lower() == "lisbon"
        assert len(itinerary.days) == 3

        all_stops = [s for day in itinerary.days for s in day.stops]
        niche_stops = [s for s in all_stops if s.is_niche]

        # Verify that at least some stops are verified hidden gems with attached score
        assert len(niche_stops) >= 1, "Expected at least 1 hidden gem in final itinerary"
        for ns in niche_stops:
            assert ns.niche_score is not None
            assert 0.0 <= ns.niche_score.hidden_gem_score <= 1.0

    asyncio.run(run())
