"""
Planner Agent — Phase 1
Takes a list of Stop objects from places_tool and groups them into day plans.

Algorithm:
1. K-means clustering on lat/lon coordinates (k = num_days) to create geo-groups
2. Each cluster → one day (geographically coherent, avoids zig-zagging)
3. Gemini 2.5 Flash assigns: day theme, stop ordering (by opening hours heuristic),
   narration stub, and per-day cost estimate

Falls back to simple sequential splitting if no LLM key is set.
"""
from __future__ import annotations
import os
import uuid
import json
import re
import random
from datetime import datetime, timedelta
from typing import Optional

from app.graph.state import TravelGraphState
from app.models.schemas import (
    TripRequest, Stop, DayPlan, Itinerary, AgentEvent, TravelStyle
)
from app.tools.places_tool import get_places_for_destination

GEMINI_KEY = os.getenv("GOOGLE_API_KEY", "")

# ── K-means clustering (pure Python, no numpy needed) ────────────────────────
def _kmeans_cluster(stops: list[Stop], k: int, iterations: int = 30) -> list[list[Stop]]:
    """
    Simple k-means on (lat, lon) coordinates.
    Returns k lists of stops (clusters).
    """
    if k >= len(stops):
        return [[s] for s in stops]

    # Initialise centroids using k-means++ seeding
    centroids = [{"lat": stops[0].lat, "lon": stops[0].lon}]
    for _ in range(1, k):
        distances = []
        for s in stops:
            d = min(_dist(s, c) for c in centroids)
            distances.append(d)
        total = sum(distances)
        if total == 0:
            centroids.append({"lat": stops[len(centroids)].lat, "lon": stops[len(centroids)].lon})
            continue
        probs = [d / total for d in distances]
        # weighted random choice
        r = random.random()
        cumul = 0
        for i, p in enumerate(probs):
            cumul += p
            if r <= cumul:
                centroids.append({"lat": stops[i].lat, "lon": stops[i].lon})
                break

    # Iterate
    for _ in range(iterations):
        clusters: list[list[Stop]] = [[] for _ in range(k)]
        for stop in stops:
            nearest = min(range(k), key=lambda i: _dist(stop, centroids[i]))
            clusters[nearest].append(stop)

        # Recompute centroids
        new_centroids = []
        for i, cluster in enumerate(clusters):
            if cluster:
                new_centroids.append({
                    "lat": sum(s.lat for s in cluster) / len(cluster),
                    "lon": sum(s.lon for s in cluster) / len(cluster),
                })
            else:
                new_centroids.append(centroids[i])  # keep old if empty
        centroids = new_centroids

    # Final assignment
    clusters = [[] for _ in range(k)]
    for stop in stops:
        nearest = min(range(k), key=lambda i: _dist(stop, centroids[i]))
        clusters[nearest].append(stop)

    return [c for c in clusters if c]  # remove empty clusters


def _dist(stop: Stop, centroid: dict) -> float:
    """Euclidean distance on lat/lon (good enough for city-scale)."""
    return ((stop.lat - centroid["lat"]) ** 2 + (stop.lon - centroid["lon"]) ** 2) ** 0.5


# ── Theme assignment via Gemini ───────────────────────────────────────────────
async def _assign_day_themes(clusters: list[list[Stop]], destination: str) -> list[str]:
    """Use Gemini 2.5 Flash to assign evocative day themes. Falls back to heuristic."""
    if not GEMINI_KEY:
        return _heuristic_themes(clusters)

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite-preview-06-17",
            google_api_key=GEMINI_KEY,
            temperature=0.7,
        )

        cluster_summaries = []
        for i, stops in enumerate(clusters):
            categories = list({s.category for s in stops})
            names = [s.name for s in stops[:4]]
            cluster_summaries.append(f"Day {i+1}: {', '.join(names)} (categories: {', '.join(categories)})")

        prompt = f"""For a trip to {destination}, assign a short evocative 2-4 word day theme for each day based on its stops.
Return ONLY a JSON array of strings, one theme per day.

Days:
{chr(10).join(cluster_summaries)}

Example: ["Historic Discoveries", "Hidden Locals", "Coastal Wonders"]"""

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        raw = response.content.strip()
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            themes = json.loads(match.group())
            if len(themes) >= len(clusters):
                return themes[:len(clusters)]

    except Exception as e:
        print(f"[planner_agent] Theme assignment failed: {e}")

    return _heuristic_themes(clusters)


def _heuristic_themes(clusters: list[list[Stop]]) -> list[str]:
    """Fallback themes based on dominant stop categories."""
    theme_map = {
        "attraction": "Historic Discoveries",
        "museum":     "Arts & Culture",
        "park":       "Nature & Gardens",
        "restaurant": "Food & Markets",
        "viewpoint":  "Panoramic Views",
        "market":     "Local Markets",
        "beach":      "Coastal Escape",
    }
    themes = []
    for cluster in clusters:
        category_counts: dict[str, int] = {}
        for s in cluster:
            category_counts[s.category] = category_counts.get(s.category, 0) + 1
        dominant = max(category_counts, key=category_counts.get)
        themes.append(theme_map.get(dominant, "Exploration Day"))
    return themes


# ── Narration via Gemini ──────────────────────────────────────────────────────
async def _generate_narrations(stops: list[Stop], destination: str) -> list[str]:
    """Generate 1-sentence atmospheric narration per stop. Falls back to description."""
    if not GEMINI_KEY or len(stops) > 12:  # skip if too many stops (cost control)
        return [s.description for s in stops]

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite-preview-06-17",
            google_api_key=GEMINI_KEY,
            temperature=0.8,
        )

        stops_desc = "\n".join([
            f"- {s.name} ({s.category}, {s.duration_minutes}min)"
            for s in stops
        ])

        prompt = f"""Write one short, atmospheric 1-sentence travel narration for each stop in {destination}.
Make them evocative and specific — not generic descriptions. Use present tense.
Return ONLY a JSON array of strings, one per stop.

Stops:
{stops_desc}"""

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        raw = response.content.strip()
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            narrations = json.loads(match.group())
            if len(narrations) >= len(stops):
                return narrations[:len(stops)]

    except Exception as e:
        print(f"[planner_agent] Narration failed: {e}")

    return [s.description for s in stops]


# ── Max stops per day by pace ─────────────────────────────────────────────────
PACE_LIMITS = {"slow": 3, "moderate": 5, "fast": 7}


# ── Main planner node ─────────────────────────────────────────────────────────
async def planner_node(state: TravelGraphState) -> dict:
    """
    Phase 1 planner:
    1. Fetch real places from OpenTripMap (+ Google Places enrichment)
    2. K-means cluster into days
    3. Assign themes via Gemini 2.5 Flash (or heuristic fallback)
    4. Generate narrations via Gemini (or use descriptions)
    5. Build Itinerary
    """
    events = list(state.get("events", []))
    trip: TripRequest = state["trip_request"]

    events.append(AgentEvent(
        event_type="agent_start",
        agent="planner_agent",
        message=f"Discovering places in {trip.destination}...",
    ))

    # ── Fetch places ──────────────────────────────────────────────────────────
    stops = await get_places_for_destination(
        destination=trip.destination,
        num_days=trip.num_days,
        travel_style=trip.travel_style.value if trip.travel_style else "balanced",
    )

    events.append(AgentEvent(
        event_type="agent_step",
        agent="planner_agent",
        message=f"Found {len(stops)} places — building your {trip.num_days}-day plan...",
    ))

    # ── Cluster into days ─────────────────────────────────────────────────────
    max_per_day = PACE_LIMITS.get(trip.pace.value if trip.pace else "moderate", 5)
    desired_stops = min(trip.num_days * max_per_day, len(stops))
    stops_to_plan = stops[:desired_stops]

    clusters = _kmeans_cluster(stops_to_plan, k=trip.num_days)

    # ── Assign themes ─────────────────────────────────────────────────────────
    themes = await _assign_day_themes(clusters, trip.destination)

    events.append(AgentEvent(
        event_type="agent_step",
        agent="planner_agent",
        message=f"Assigned day themes: {', '.join(themes[:3])}{'...' if len(themes) > 3 else ''}",
    ))

    # ── Narrations ────────────────────────────────────────────────────────────
    all_stops_flat = [s for cluster in clusters for s in cluster]
    narrations = await _generate_narrations(all_stops_flat, trip.destination)
    narration_map = {s.id: n for s, n in zip(all_stops_flat, narrations)}

    # ── Build days ────────────────────────────────────────────────────────────
    days: list[DayPlan] = []
    start_date = datetime.utcnow()

    for day_idx, (cluster, theme) in enumerate(zip(clusters, themes)):
        # Trim to pace limit
        day_stops = cluster[:max_per_day]

        # Attach narrations, calculate travel times (stub: 15min between each)
        for i, stop in enumerate(day_stops):
            stop.narration = narration_map.get(stop.id, stop.description)
            if i > 0:
                stop.travel_time_from_prev_minutes = 15  # Phase 3 will use real routing

        daily_cost = sum(
            (s.estimated_cost_usd or 0) for s in day_stops
        )

        day = DayPlan(
            day_number=day_idx + 1,
            theme=theme,
            date=(start_date + timedelta(days=day_idx)).date().isoformat(),
            stops=day_stops,
            daily_cost_estimate_usd=daily_cost,
        )
        days.append(day)

    total_cost = sum(d.daily_cost_estimate_usd or 0 for d in days)

    itinerary = Itinerary(
        id=str(uuid.uuid4()),
        trip_request=trip,
        days=days,
        total_cost_estimate_usd=total_cost,
        created_at=datetime.utcnow().isoformat(),
    )

    niche_count = sum(1 for d in days for s in d.stops if s.is_niche)

    events.append(AgentEvent(
        event_type="itinerary_ready",
        agent="planner_agent",
        message=(
            f"Your {trip.num_days}-day {trip.destination} itinerary is ready! "
            f"{sum(len(d.stops) for d in days)} stops planned"
            + (f", {niche_count} hidden gems" if niche_count else "")
            + f". Estimated cost: ${total_cost:,.0f}."
        ),
    ))

    return {"itinerary": itinerary, "events": events}
