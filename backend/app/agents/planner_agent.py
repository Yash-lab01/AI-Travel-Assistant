"""
Planner Agent — Phase 3
Takes a list of Stop objects (ranked or places) and structures them into geographically coherent day plans.

Algorithm:
1. K-means clustering on lat/lon coordinates (k = num_days) to create geo-groups
2. Each cluster -> one day (geographically coherent, avoids cross-city zig-zagging)
3. Gemini 2.5 Flash assigns: day theme, stop ordering, narration stubs, and per-day cost estimate
4. Routing Tool calculates realistic walking/transit times between sequential stops
5. Weather Tool fetches real daily forecasts via Open-Meteo
"""
from __future__ import annotations
import os
import uuid
import json
import re
import random
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.graph.state import TravelGraphState
from app.models.schemas import (
    TripRequest, Stop, DayPlan, Itinerary, AgentEvent, TravelStyle
)
from app.tools.places_tool import get_places_for_destination
from app.tools.routing_tool import calculate_sequential_transit_times
from app.tools.weather_tool import get_daily_weather_forecast

GEMINI_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")


# ── K-means clustering (pure Python, no numpy needed) ────────────────────────
def _kmeans_cluster(stops: list[Stop], k: int, iterations: int = 30) -> list[list[Stop]]:
    """
    Cluster stops into k geographically coherent groups using lat/lon coordinates.
    Guarantees every cluster has at least one stop.
    """
    if not stops:
        return [[] for _ in range(k)]
    if len(stops) <= k:
        return [[s] for s in stops] + [[] for _ in range(k - len(stops))]

    # Initialise centroids by picking k evenly spaced stops sorted by latitude
    sorted_stops = sorted(stops, key=lambda s: (s.lat, s.lon))
    step = len(sorted_stops) // k
    centroids = [(sorted_stops[i * step].lat, sorted_stops[i * step].lon) for i in range(k)]

    assignments = [0] * len(stops)

    for _ in range(iterations):
        # Assign each stop to the nearest centroid
        for i, stop in enumerate(stops):
            min_dist = float("inf")
            best_c = 0
            for c_idx, (c_lat, c_lon) in enumerate(centroids):
                dist = (stop.lat - c_lat) ** 2 + (stop.lon - c_lon) ** 2
                if dist < min_dist:
                    min_dist = dist
                    best_c = c_idx
            assignments[i] = best_c

        # Recompute centroids
        new_centroids = []
        for c_idx in range(k):
            cluster_members = [stops[i] for i, a in enumerate(assignments) if a == c_idx]
            if cluster_members:
                avg_lat = sum(s.lat for s in cluster_members) / len(cluster_members)
                avg_lon = sum(s.lon for s in cluster_members) / len(cluster_members)
                new_centroids.append((avg_lat, avg_lon))
            else:
                new_centroids.append(centroids[c_idx])
        centroids = new_centroids

    # Build result clusters
    clusters: list[list[Stop]] = [[] for _ in range(k)]
    for i, a in enumerate(assignments):
        clusters[a].append(stops[i])

    # Rebalance empty clusters by stealing from the largest cluster
    for c_idx in range(k):
        if not clusters[c_idx]:
            largest = max(range(k), key=lambda idx: len(clusters[idx]))
            if len(clusters[largest]) > 1:
                clusters[c_idx].append(clusters[largest].pop())

    return [c for c in clusters if c]


# ── Theme generation with Gemini ─────────────────────────────────────────────
async def _assign_day_themes(
    clusters: list[list[Stop]],
    destination: str,
    region_pref: Optional[str] = None,
) -> list[str]:
    """Use Gemini 2.5 Flash to generate an evocative theme for each day cluster."""
    if not clusters:
        return []

    cluster_summaries = []
    for i, cluster in enumerate(clusters):
        names = [s.name for s in cluster[:4]]
        categories = list(set(s.category for s in cluster))
        cluster_summaries.append(f"Day {i+1}: stops=[{', '.join(names)}], types=[{', '.join(categories)}]")

    if GEMINI_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage

            llm = ChatGoogleGenerativeAI(
                model="gemini-3.5-flash",
                google_api_key=GEMINI_KEY,
                temperature=0.4,
            )


            prompt = f"""You are an evocative travel writer. Give each day of this {destination} itinerary a short, evocative theme (3-6 words).
{f"Traveler preference: {region_pref}" if region_pref else ""}

Clusters:
{chr(10).join(cluster_summaries)}

Return ONLY a JSON array of strings, one per day. Example: ["Historic Alfama & Fado Echoes", "Coastal Heights & Hidden Miradouros"]"""

            response = await llm.ainvoke([HumanMessage(content=prompt)])
            raw = response.content.strip()
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                themes = json.loads(match.group())
                if len(themes) == len(clusters):
                    return themes
        except Exception as e:
            print(f"[planner_agent] Theme generation failed: {e}")

    # Fallback heuristic themes
    default_themes = [
        "Historic Quarters & Local Heritage",
        "Scenic Heights & Panoramic Viewpoints",
        "Coastal Breezes & Hidden Cafes",
        "Artisanal Markets & Cultural Wonders",
        "Offbeat Secrets & Sunset Trails",
        "Royal Landmarks & Sacred Enclaves",
        "Culinary Discoveries & Cobblestone Walks",
    ]
    return [default_themes[i % len(default_themes)] for i in range(len(clusters))]


# ── Narration generation with Gemini ─────────────────────────────────────────
async def _generate_narrations(stops: list[Stop], destination: str) -> list[str]:
    """Generate 1-2 sentence atmospheric narration for each stop."""
    if not stops:
        return []

    if not GEMINI_KEY:
        return [s.description for s in stops]

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            google_api_key=GEMINI_KEY,
            temperature=0.3,
        )


        stops_desc = "\n".join(
            f"- {s.name} ({s.category}): {s.description}" for s in stops
        )

        prompt = f"""Write a 1-2 sentence atmospheric, vivid narration for each of these stops in {destination}.
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


PACE_LIMITS = {"slow": 3, "relaxed": 3, "moderate": 5, "fast": 7, "intense": 7}


# ── Main planner node ─────────────────────────────────────────────────────────
async def planner_node(state: TravelGraphState) -> dict:
    """
    Phase 3 planner:
    1. Use ranked_stops from Ranker Agent (or fetch from OpenTripMap fallback)
    2. K-means cluster into geographically coherent days
    3. Assign themes via Gemini 2.5 Flash
    4. Generate narrations via Gemini
    5. Calculate realistic transit times between consecutive stops via routing tool
    6. Attach Open-Meteo daily weather notes to each day
    7. Build complete Itinerary
    """
    events = list(state.get("events", []))
    trip: TripRequest = state["trip_request"]

    events.append(AgentEvent(
        event_type="agent_start",
        agent="planner_agent",
        message=f"Structuring geo-clustered daily plan for {trip.destination}...",
    ))

    # 1. Use Ranked Stops or Fetch Places Fallback
    ranked = state.get("ranked_stops")
    if ranked and len(ranked) > 0:
        stops = list(ranked)
    else:
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

    # 2. Cluster into days
    max_per_day = PACE_LIMITS.get(trip.pace.value if trip.pace else "moderate", 5)
    desired_stops = min(trip.num_days * max_per_day, len(stops))
    stops_to_plan = stops[:desired_stops]

    clusters = _kmeans_cluster(stops_to_plan, k=trip.num_days)

    # 3. Assign themes
    themes = await _assign_day_themes(clusters, trip.destination, trip.region_preference)

    events.append(AgentEvent(
        event_type="agent_step",
        agent="planner_agent",
        message=f"Assigned day themes: {', '.join(themes[:3])}{'...' if len(themes) > 3 else ''}",
    ))

    # 4. Narrations
    all_stops_flat = [s for cluster in clusters for s in cluster]
    narrations = await _generate_narrations(all_stops_flat, trip.destination)
    narration_map = {s.id: n for s, n in zip(all_stops_flat, narrations)}

    # 5. Weather forecast for destination center
    center_lat = stops[0].lat if stops else 38.7223
    center_lon = stops[0].lon if stops else -9.1393
    weather_notes = await get_daily_weather_forecast(center_lat, center_lon, num_days=trip.num_days)

    # 6. Build days with transit times & weather notes
    days: list[DayPlan] = []
    start_date = datetime.now(timezone.utc)

    for day_idx, (cluster, theme) in enumerate(zip(clusters, themes)):
        day_stops = cluster[:max_per_day]

        # Attach narrations
        for stop in day_stops:
            stop.narration = narration_map.get(stop.id, stop.description)

        # Calculate realistic walking/transit times between sequential stops
        day_stops = calculate_sequential_transit_times(day_stops)

        daily_cost = sum((s.estimated_cost_usd or 0) for s in day_stops)
        weather_note = weather_notes[day_idx] if day_idx < len(weather_notes) else None

        day = DayPlan(
            day_number=day_idx + 1,
            theme=theme,
            date=(start_date + timedelta(days=day_idx)).date().isoformat(),
            stops=day_stops,
            day_cost_estimate_usd=daily_cost,
            weather_note=weather_note,
        )
        days.append(day)

    total_cost = sum(d.day_cost_estimate_usd or 0 for d in days)

    itinerary = Itinerary(
        id=str(uuid.uuid4()),
        trip_request=trip,
        days=days,
        total_cost_estimate_usd=total_cost,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    niche_count = sum(1 for d in days for s in d.stops if s.is_niche)

    events.append(AgentEvent(
        event_type="itinerary_ready",
        agent="planner_agent",
        message=(
            f"Your {trip.num_days}-day {trip.destination} itinerary is ready! "
            f"Featuring {niche_count} hidden gems, live transit pacing, and weather forecasts."
        ),
    ))

    return {
        "itinerary": itinerary,
        "events": events,
    }
