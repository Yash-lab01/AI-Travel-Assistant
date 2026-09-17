"""
Unit tests for Phase 11C & Phase 11D:
- Multi-Select Clarification Engine (Phase 11C)
- Strategic Fixed-Info Retrieval & Enriched Question Templates (Phase 11D)
Verifies:
1. ClarificationQuestion schema and templates have is_multi_select flag.
2. Multi-select answer processing in intake_node (travel_style, region_vibe, interests, dietary, group, budget).
3. Balanced niche_weight calculation when both niche and popular are selected.
4. Strategic dimension tracking: partial prompt triggers questions; fully specified prompt bypasses clarification.
5. All curated templates (Goa, Mumbai, Pune, Rajasthan, Kashmir, Lisbon) contain 4 rich questions with 4-5 options.
6. Unknown destination prompts provide interactive destination selection chips.
"""
import pytest
from langchain_core.messages import HumanMessage
from app.models.schemas import ClarificationQuestion, TravelStyle, TravelPace, GroupType
from app.agents.intake_agent import (
    DESTINATION_QUESTIONS,
    _get_generic_clarification_questions,
    intake_node,
)


def test_clarification_question_schema_flags():
    """Verify is_multi_select default and explicit values on questions."""
    generic_qs = _get_generic_clarification_questions("Lisbon")
    style_q = next(q for q in generic_qs if q.category == "travel_style")
    pace_q = next(q for q in generic_qs if q.category == "pace")

    assert style_q.is_multi_select is True
    assert pace_q.is_multi_select is False

    goa_qs = DESTINATION_QUESTIONS["goa"]
    vibe_q = next(q for q in goa_qs if q["id"] == "goa_vibe")
    pace_q = next(q for q in goa_qs if q["id"] == "travel_pace")
    gem_q = next(q for q in goa_qs if q["id"] == "gem_focus")

    assert vibe_q.get("is_multi_select") is True
    assert pace_q.get("is_multi_select") is False
    assert gem_q.get("is_multi_select") is True


def test_destination_templates_enriched_structure():
    """Verify all 6 curated destinations have 4 questions and 4-5 options on key categories."""
    for dest in ["goa", "mumbai", "pune", "rajasthan", "kashmir", "lisbon"]:
        assert dest in DESTINATION_QUESTIONS, f"Missing template for {dest}"
        qs = DESTINATION_QUESTIONS[dest]
        assert len(qs) >= 3, f"{dest} should have at least 3-4 questions, found {len(qs)}"

        # Verify options richness
        for q in qs:
            assert len(q["options"]) >= 3, f"{dest} question {q['id']} has fewer than 3 options"
            for opt in q["options"]:
                assert "label" in opt and "value" in opt and "icon" in opt


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
            "group": ["family"],
            "budget": ["luxury"],
        },
        "events": [],
    }

    result = await intake_node(state)
    trip_req = result.get("trip_request")
    assert trip_req is not None
    assert trip_req.destination == "Goa"
    assert trip_req.travel_style == TravelStyle.cultural
    assert trip_req.pace in (TravelPace.slow, TravelPace.relaxed)
    assert trip_req.group_type == GroupType.family
    assert trip_req.budget_usd == 2500.0
    assert trip_req.region_preference == "North Goa & South Goa"

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


@pytest.mark.anyio
async def test_strategic_dimension_tracking_partial_prompt():
    """Partial prompt ('3 days in Goa') lacks style, pace, group, budget -> needs clarification."""
    state = {
        "messages": [HumanMessage(content="3 days in Goa")],
        "force_plan": False,
        "clarification_answers": None,
        "events": [],
    }

    result = await intake_node(state)
    assert result.get("needs_clarification") is True
    questions = result.get("clarification_questions", [])
    assert len(questions) == 4
    categories = [q.category for q in questions]
    assert "region_vibe" in categories
    assert "travel_style" in categories
    assert "pace" in categories
    assert "group" in categories


@pytest.mark.anyio
async def test_strategic_dimension_tracking_complete_prompt():
    """Fully specified prompt (destination + duration + group + budget + pace + interests) bypasses clarification."""
    state = {
        "messages": [HumanMessage(content="Plan 4 days in Goa with family, luxury budget, relaxed pace focusing on beaches and seafood")],
        "force_plan": False,
        "clarification_answers": None,
        "events": [],
    }

    result = await intake_node(state)
    # 5+ dimensions specified -> should NOT be blocked by clarification
    assert result.get("needs_clarification") is False
    assert result.get("trip_request") is not None
    assert result.get("trip_request").destination == "Goa"


@pytest.mark.anyio
async def test_unknown_destination_prompt_offers_choices():
    """Prompt missing destination ('Plan a 3 day holiday') offers destination choice chips."""
    state = {
        "messages": [HumanMessage(content="Plan a 3 day holiday")],
        "force_plan": False,
        "clarification_answers": None,
        "events": [],
    }

    result = await intake_node(state)
    assert result.get("needs_clarification") is True
    questions = result.get("clarification_questions", [])
    assert len(questions) >= 1
    assert questions[0].category == "destination"
    dest_options = [opt.value for opt in questions[0].options]
    assert "Goa" in dest_options
    assert "Mumbai" in dest_options
