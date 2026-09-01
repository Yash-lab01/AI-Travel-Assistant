"""
Planner Agent — Phase 3
Takes a list of Stop objects (ranked or places) and structures them into geographically coherent day plans.

Algorithm:
1. K-means++ clustering on lat/lon coordinates (k = num_days) to create balanced geo-groups
2. Guarantees exactly k non-empty day clusters with balanced stop counts
3. Gemini 3.5 Flash assigns: day theme, stop ordering, narration stubs, and per-day cost estimate
4. Routing Tool calculates realistic walking/transit times between sequential stops
5. Weather Tool fetches real daily forecasts via Open-Meteo
"""
from __future__ import annotations
import os
import uuid
import json
import re
import random
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, Any

from app.graph.state import TravelGraphState
from app.models.schemas import (
    TripRequest, Stop, DayPlan, Itinerary, AgentEvent, TravelStyle
)
from app.tools.places_tool import get_places_for_destination
from app.tools.routing_tool import calculate_sequential_transit_times
from app.tools.weather_tool import get_daily_weather_forecast
from app.tools.destination_images import get_destination_banner

GEMINI_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")


def safe_extract_text(content: Any) -> str:
    """Safely extract string text from LLM response (handles str, list of dicts, or list of parts)."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, dict):
                parts.append(p.get("text", ""))
            elif hasattr(p, "text"):
                parts.append(getattr(p, "text", ""))
            else:
                parts.append(str(p))
        return "".join(parts).strip()
    return str(content).strip()


# ── K-means++ clustering (balanced, guarantees k non-empty clusters) ──────────
def _kmeans_plus_plus_init(stops: list[Stop], k: int) -> list[tuple[float, float]]:
    """
    K-means++ centroid initialization.
    Picks seeds that are maximally spread to prevent Day 1 geographic clustering bias.
    """
    import random as rnd
    centroids = []
    # Pick first centroid randomly from the stops
    first = rnd.choice(stops)
    centroids.append((first.lat, first.lon))

    for _ in range(k - 1):
        # Compute squared distances from each stop to its nearest centroid
        distances = []
        for stop in stops:
            min_dist = min(
                (stop.lat - c_lat) ** 2 + (stop.lon - c_lon) ** 2
                for c_lat, c_lon in centroids
            )
            distances.append(min_dist)

        # Sample proportional to squared distance — far stops are more likely seeds
        total = sum(distances)
        if total == 0:
            next_stop = rnd.choice(stops)
        else:
            probs = [d / total for d in distances]
            cumulative = 0.0
            r = rnd.random()
            next_stop = stops[-1]
            for stop, prob in zip(stops, probs):
                cumulative += prob
                if r <= cumulative:
                    next_stop = stop
                    break
        centroids.append((next_stop.lat, next_stop.lon))

    return centroids


def _kmeans_cluster(stops: list[Stop], k: int, iterations: int = 40) -> list[list[Stop]]:
    """
    Cluster stops into k geographically coherent groups using K-means++.
    Guarantees that the returned list has EXACTLY k non-empty, balanced clusters.
    """
    if not stops:
        return [[] for _ in range(k)]

    # If fewer stops than days, assign each to a day and pad
    if len(stops) <= k:
        clusters = [[s] for s in stops]
        while len(clusters) < k:
            clusters.append([stops[len(clusters) % len(stops)]])
        return clusters[:k]

    # K-means++ initialization (maximally spread centroids)
    centroids = _kmeans_plus_plus_init(stops, k)
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

    # Rebalance: steal from the largest cluster to fill empty clusters
    for c_idx in range(k):
        if not clusters[c_idx]:
            largest = max(range(k), key=lambda idx: len(clusters[idx]))
            if len(clusters[largest]) > 1:
                clusters[c_idx].append(clusters[largest].pop())
            elif clusters[largest]:
                clusters[c_idx].append(clusters[largest][0])

    # Balance stop counts across days (reduce extreme variance)
    total_stops = sum(len(c) for c in clusters)
    target_per_day = max(1, total_stops // k)

    # If any cluster has > 2x the target, redistribute to undersized ones
    for _ in range(3):  # up to 3 rebalance passes
        for c_idx in range(k):
            while len(clusters[c_idx]) > target_per_day + 2:
                # Find smallest cluster
                smallest = min(range(k), key=lambda idx: len(clusters[idx]))
                if smallest == c_idx:
                    break
                clusters[smallest].append(clusters[c_idx].pop())

    # Final guarantee: exactly k non-empty clusters
    result = [c for c in clusters if c]
    while len(result) < k:
        result.append([stops[len(result) % len(stops)]])

    return result[:k]


# ── Theme generation with Gemini ──────────────────────────────────────────────
async def _assign_day_themes(
    clusters: list[list[Stop]],
    destination: str,
    region_pref: Optional[str] = None,
) -> list[str]:
    """Use Gemini 3.5 Flash to generate an evocative theme for each day cluster."""
    if not clusters:
        return []

    cluster_summaries = []
    for i, cluster in enumerate(clusters):
        names = [s.name for s in cluster[:5]]
        categories = list(set(s.category for s in cluster))
        cluster_summaries.append(f"Day {i+1}: stops=[{', '.join(names)}], types=[{', '.join(categories)}]")

    if GEMINI_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage, SystemMessage

            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=GEMINI_KEY,
                temperature=0.5,
            )

            prompt = f"""You are an evocative travel writer. Give each day of this {destination} itinerary a unique, short, evocative theme (3-6 words). Each theme must be DIFFERENT and specific to the stops listed.
{f"Traveler preference: {region_pref}" if region_pref else ""}

Clusters:
{chr(10).join(cluster_summaries)}

Return ONLY a valid JSON array of strings, one per day. No markdown, no explanation.
Example for 3 days: ["Heritage Lanes & Sacred Temples", "Coastal Promenades & Colonial Grandeur", "Hill Views & Artisan Bazaars"]"""

            response = await llm.ainvoke([HumanMessage(content=prompt)])
            raw = safe_extract_text(response.content)
            # Strip markdown code fences if present
            raw = re.sub(r'```(?:json)?', '', raw).strip('`').strip()
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                themes = json.loads(match.group())
                if isinstance(themes, list) and len(themes) == len(clusters):
                    # Ensure all are non-empty strings
                    themes = [t if isinstance(t, str) and t.strip() else f"Day {i+1} Discovery" for i, t in enumerate(themes)]
                    return themes
        except Exception as e:
            print(f"[planner_agent] Theme generation failed: {e}")

    # Context-aware fallback themes based on destination
    dest_lower = destination.lower()
    if any(x in dest_lower for x in ["mumbai", "bombay"]):
        fallbacks = ["Colonial Heritage & Gateway Grandeur", "Bandra Coastline & Bohemian Cafes", "Bazaars, Bollywood & Dharavi Life"]
    elif "pune" in dest_lower:
        fallbacks = ["Peshwa Heritage & Temple Trails", "Hill Forts & Café Culture", "Museums & Koregaon Park Gardens"]
    elif "goa" in dest_lower:
        fallbacks = ["Colonial Panjim & Latin Quarter", "North Beach Shacks & Anjuna Flea", "South Goa Coves & Spice Estates"]
    elif "delhi" in dest_lower:
        fallbacks = ["Mughal Monuments & Old Delhi Bazaars", "Lutyens' Delhi & Cultural Hubs", "South Delhi Ruins & Modern Art Spaces"]
    elif "jaipur" in dest_lower or "rajasthan" in dest_lower:
        fallbacks = ["Pink City Palaces & Stepwells", "Amer Fort Heights & Hill Temples", "Sunset Nahargarh & Blue Pottery Markets"]
    elif "kerala" in dest_lower:
        fallbacks = ["Fort Kochi Heritage & Spice Wharfs", "Munnar Tea Hills & Wildlife Sanctuaries", "Alleppey Backwaters & Houseboat Drifts"]
    elif "bali" in dest_lower:
        fallbacks = ["Ubud Rice Terraces & Sacred Temples", "Seminyak Sunsets & Surf Culture", "Uluwatu Cliffs & Spiritual Ceremonies"]
    elif "lisbon" in dest_lower:
        fallbacks = ["Alfama Fado & Castelo Views", "Baixa Shopping & Riverside Cafes", "Belém Towers & Custard Tart Trails"]
    else:
        fallbacks = [
            f"Historic {destination} Heritage & Temples",
            f"{destination} Viewpoints & Local Cuisine",
            f"Hidden {destination} Gems & Markets",
            "Cultural Discoveries & Evening Strolls",
            "Offbeat Trails & Artisan Enclaves",
        ]

    return [fallbacks[i % len(fallbacks)] for i in range(len(clusters))]


# ── Narration generation (Local Ollama fine-tuned -> Gemini 3.5 Flash -> Fallback) ──
async def _generate_narrations(stops: list[Stop], destination: str) -> list[str]:
    """Generate 1-2 sentence atmospheric narration for each stop."""
    if not stops:
        return []

    # 1. Try Local Ollama fine-tuned model first if running
    try:
        from app.tools.ollama_narrator import generate_stop_narrations_batch, is_ollama_available
        if await is_ollama_available():
            ollama_narrations = await generate_stop_narrations_batch(stops, destination)
            if all(n is not None for n in ollama_narrations):
                print(f"[planner_agent] Successfully generated {len(stops)} narrations using local Ollama model")
                return [n for n in ollama_narrations if n is not None]
    except Exception as oe:
        print(f"[planner_agent] Local Ollama narration notice: {oe}")

    # 2. Try Gemini 2.5 Flash
    if GEMINI_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage

            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=GEMINI_KEY,
                temperature=0.35,
            )

            stops_desc = "\n".join(
                f"- {s.name} ({s.category}): {s.description}" for s in stops
            )

            prompt = f"""Write a 1-2 sentence atmospheric, vivid narration for each of these stops in {destination}.
Make them evocative and specific — no generic phrases like "a must-see landmark". Use present tense. Reference the stop's actual character.
Return ONLY a valid JSON array of strings, one per stop. No markdown.

Stops:
{stops_desc}"""

            response = await llm.ainvoke([HumanMessage(content=prompt)])
            raw = safe_extract_text(response.content)
            raw = re.sub(r'```(?:json)?', '', raw).strip('`').strip()
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                narrations = json.loads(match.group())
                if len(narrations) >= len(stops):
                    return narrations[:len(stops)]

        except Exception as e:
            print(f"[planner_agent] Gemini narration failed: {e}")

    return [s.description for s in stops]


PACE_LIMITS = {"slow": 3, "relaxed": 3, "moderate": 5, "fast": 7, "intense": 7}


# ── Main planner node ─────────────────────────────────────────────────────────
async def planner_node(state: TravelGraphState) -> dict:
    """
    Phase 3 planner:
    1. Use ranked_stops from Ranker Agent (ALWAYS — ranker is responsible for fetching OTM + niche blending)
    2. K-means++ cluster into geographically coherent, balanced days (guaranteed k days)
    3. Assign destination-aware themes via Gemini 3.5 Flash
    4. Generate vivid narrations via Gemini 3.5 Flash
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

    # 1. ALWAYS use ranked_stops from Ranker Agent
    # The Ranker is responsible for fetching OTM places AND blending niche spots.
    # Planner should NEVER bypass it by fetching its own stops.
    ranked = state.get("ranked_stops")
    if not ranked or len(ranked) == 0:
        # Only use direct OTM fetch as true last resort (e.g. ranker node errored out)
        print(f"[planner_agent] WARNING: ranked_stops is empty — falling back to direct OTM fetch for {trip.destination}")
        stops = await get_places_for_destination(
            destination=trip.destination,
            num_days=trip.num_days,
            travel_style=trip.travel_style.value if trip.travel_style else "balanced",
        )
    else:
        stops = list(ranked)

    # Deduplicate by name (case-insensitive) to prevent duplicate stops across days
    seen_names: set[str] = set()
    unique_stops: list[Stop] = []
    for s in stops:
        norm = s.name.strip().lower()
        if norm not in seen_names:
            seen_names.add(norm)
            unique_stops.append(s)
    stops = unique_stops

    events.append(AgentEvent(
        event_type="agent_step",
        agent="planner_agent",
        message=f"Found {len(stops)} unique places — building your {trip.num_days}-day plan...",
    ))

    # 2. Cluster into balanced days using K-means++
    max_per_day = PACE_LIMITS.get(trip.pace.value if trip.pace else "moderate", 5)
    desired_stops = min(trip.num_days * max_per_day, len(stops))
    stops_to_plan = stops[:desired_stops] if desired_stops > 0 else stops

    clusters = _kmeans_cluster(stops_to_plan, k=trip.num_days)

    # 3. Assign destination-aware themes
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

    # 5. Weather forecast — use spatial median of all stops as center
    lats = [s.lat for s in stops if s.lat]
    lons = [s.lon for s in stops if s.lon]
    center_lat = sorted(lats)[len(lats) // 2] if lats else 18.5204
    center_lon = sorted(lons)[len(lons) // 2] if lons else 73.8567
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

        # Cover photo for day: use first stop's photo or destination banner
        day_cover = (
            day_stops[0].photo_urls[0]
            if (day_stops and day_stops[0].photo_urls and day_stops[0].photo_urls[0])
            else get_destination_banner(trip.destination)
        )

        day = DayPlan(
            day_number=day_idx + 1,
            theme=theme,
            date=(start_date + timedelta(days=day_idx)).date().isoformat(),
            stops=day_stops,
            day_cost_estimate_usd=daily_cost,
            weather_note=weather_note,
            cover_image_url=day_cover,
        )
        days.append(day)

    total_cost = sum(d.day_cost_estimate_usd or 0 for d in days)

    itinerary = Itinerary(
        id=str(uuid.uuid4()),
        trip_request=trip,
        days=days,
        total_cost_estimate_usd=total_cost,
        created_at=datetime.now(timezone.utc).isoformat(),
        cover_image_url=get_destination_banner(trip.destination),
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
