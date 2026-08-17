"""
Ranker Agent — Phase 2
Blends mainstream attractions (OpenTripMap/Google Places) with authentic hidden gems
(Reddit/Tavily scored via log-normalized formula) according to the user's niche_weight.
"""
from __future__ import annotations
import asyncio
from typing import Optional

from app.graph.state import TravelGraphState
from app.models.schemas import (
    TripRequest, Stop, AgentEvent, TravelStyle, TravelPace
)
from app.tools.places_tool import get_places_for_destination
from app.tools.niche_scraper import discover_niche_spots

PACE_STOPS_PER_DAY = {
    "slow": 3,
    "relaxed": 3,
    "moderate": 5,
    "fast": 7,
    "intense": 7,
}



async def ranker_node(state: TravelGraphState) -> dict:
    """
    Ranker LangGraph Node:
    1. Fetches mainstream tourist POIs & scraped niche gems concurrently
    2. Blends them according to `trip_request.niche_weight` (0.0 = popular, 0.5 = balanced, 1.0 = deep niche)
    3. Guarantees category diversity and spatial coherence
    4. Outputs `ranked_stops` to state for the Planner Agent
    """
    trip_req = state.get("trip_request")
    events = list(state.get("events", []))

    if not trip_req:
        destination = "Lisbon"
        num_days = 3
        niche_weight = 0.5
        pace = "moderate"
    else:
        destination = trip_req.destination or "Lisbon"
        num_days = trip_req.num_days or 3
        niche_weight = trip_req.niche_weight if trip_req.niche_weight is not None else 0.5
        pace = trip_req.pace or "moderate"

    # Emit ranker start event
    events.append(
        AgentEvent(
            agent="Ranker",
            event_type="agent_start",
            message=f"Analyzing destination '{destination}' — balancing iconic landmarks with authentic community gems...",
        )
    )

    # ── 1. Fetch Popular & Niche Spots Concurrently ───────────────────────
    popular_task = get_places_for_destination(destination, num_days=num_days)
    niche_task = discover_niche_spots(destination)


    popular_stops, niche_stops = await asyncio.gather(
        popular_task, niche_task, return_exceptions=True
    )

    if not isinstance(popular_stops, list):
        popular_stops = []
    if not isinstance(niche_stops, list):
        niche_stops = []

    # ── 2. Calculate Target Pool Size & Blending Ratio ────────────────────
    stops_per_day = PACE_STOPS_PER_DAY.get(pace, 5)
    total_needed = max(stops_per_day * num_days, 6)

    # Calculate niche proportion based on niche_weight (0.0 to 1.0)
    # niche_weight 0.0 -> ~15% niche (mostly popular)
    # niche_weight 0.5 -> ~45% niche (balanced)
    # niche_weight 1.0 -> ~75% niche (heavy gems)
    target_niche_ratio = 0.15 + (niche_weight * 0.60)
    target_niche_count = max(1, int(round(total_needed * target_niche_ratio)))
    target_popular_count = total_needed - target_niche_count

    # ── 3. Select Highest Scoring Niche Spots ─────────────────────────────
    # Sort niche spots by hidden_gem_score descending
    sorted_niche = sorted(
        niche_stops,
        key=lambda s: s.niche_score.hidden_gem_score if s.niche_score else 0.5,
        reverse=True,
    )
    selected_niche = sorted_niche[:target_niche_count]

    # ── 4. Select Diverse Popular Attractions ─────────────────────────────
    # Filter out any popular stops that duplicate selected niche names
    niche_names = {s.name.lower().strip() for s in selected_niche}
    filtered_popular = [
        s for s in popular_stops
        if s.name.lower().strip() not in niche_names
    ]

    selected_popular = filtered_popular[:target_popular_count]

    # If popular stops were fewer than target, top up with remaining niche spots
    if len(selected_popular) < target_popular_count:
        leftover_niche = sorted_niche[target_niche_count:]
        needed = target_popular_count - len(selected_popular)
        selected_popular.extend(leftover_niche[:needed])

    # ── 5. Combine & Interleave for Balanced Daily Distribution ───────────
    combined_stops: list[Stop] = []
    max_len = max(len(selected_popular), len(selected_niche))

    for idx in range(max_len):
        if idx < len(selected_popular):
            combined_stops.append(selected_popular[idx])
        if idx < len(selected_niche):
            combined_stops.append(selected_niche[idx])

    # Ensure total is sufficient
    if len(combined_stops) < total_needed and popular_stops:
        for s in popular_stops:
            if s not in combined_stops:
                combined_stops.append(s)
            if len(combined_stops) >= total_needed:
                break

    niche_count = sum(1 for s in combined_stops if s.is_niche)
    popular_count = len(combined_stops) - niche_count

    events.append(
        AgentEvent(
            agent="Ranker",
            event_type="agent_step",
            message=f"Curated {len(combined_stops)} stops: {popular_count} iconic landmarks + {niche_count} community hidden gems (Gem Weight: {niche_weight:.2f})",
        )
    )

    return {
        "ranked_stops": combined_stops,
        "events": events,
    }
