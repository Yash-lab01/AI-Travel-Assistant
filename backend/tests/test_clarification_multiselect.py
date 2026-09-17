"""
Unit tests for Phase 11C: Multi-Select Clarification Engine.
Verifies:
1. ClarificationQuestion schema and templates have is_multi_select flag.
2. Multi-select answer processing in intake_node (travel_style, region_vibe, interests, dietary).
3. Balanced niche_weight calculation when both niche and popular are selected.
"""
import pytest
from langchain_core.messages import HumanMessage
from app.models.schemas import ClarificationQuestion, TravelStyle, TravelPace
from app.agents.intake_agent import (
    DESTINATION_QUESTIONS,
    _get_generic_clarification_questions,
    intake_node,
)


def test_clarification_question_schema_flags():
    """Verify is_multi_select default and explicit values on questions."""
    # Generic questions
    generic_qs = _get_generic_clarification_questions("Lisbon")
    style_q = next(q for q in generic_qs if q.category == "travel_style")
    pace_q = next(q for q in generic_qs if q.category == "pace")

    assert style_q.is_multi_select is True
    assert pace_q.is_multi_select is False

    # Curated templates
    goa_qs = DESTINATION_QUESTIONS["goa"]
    vibe_q = next(q for q in goa_qs if q["id"] == "goa_vibe")
    pace_q = next(q for q in goa_qs if q["id"] == "travel_pace")
    gem_q = next(q for q in goa_qs if q["id"] == "gem_focus")

    assert vibe_q.get("is_multi_select") is True
    assert pace_q.get("is_multi_select") is False
    assert gem_q.get("is_multi_select") is True


@pytest.mark.anyio
async def test_intake_node_multi_select_answers():
    """Verify intake_node properly parses multi-select answers for styles, vibes, and interests."""
    state = {
        "messages": [HumanMessage(content="Plan 3 days in Goa")],
        "destination": "Goa",
        "num_days": 3,
        "force_plan": False,
        "clarification_answers": {
            "travel_style": ["cultural", "foodie"],
            "region_vibe": ["North Goa", "South Goa"],
            "interests": ["photo_spots", "markets"],
            "dietary": ["vegan"],
            "pace": ["slow"],
        },
        "events": [],
    }

    result = await intake_node(state)
    trip_req = result.get("trip_request")
    assert trip_req is not None
    assert trip_req.destination == "Goa"
    assert trip_req.travel_style == TravelStyle.cultural
    assert trip_req.pace in (TravelPace.slow, TravelPace.relaxed)
    assert trip_req.region_preference == "North Goa & South Goa"

    # All multi-selected styles, activities, and diets should be aggregated in interests
    for expected in ["cultural", "foodie", "photo_spots", "markets", "vegan food"]:
        assert expected in trip_req.interests


@pytest.mark.anyio
async def test_intake_node_niche_popular_blending():
    """Verify that selecting both niche and popular blends into balanced with 0.5 weight."""
    state = {
        "messages": [HumanMessage(content="Plan 4 days in Mumbai")],
        "destination": "Mumbai",
        "num_days": 4,
        "force_plan": False,
        "clarification_answers": {
            "travel_style": ["niche", "popular"],
        },
        "events": [],
    }

    result = await intake_node(state)
    trip_req = result.get("trip_request")
    assert trip_req is not None
    assert trip_req.travel_style == TravelStyle.balanced
    assert trip_req.niche_weight == 0.5
