"""
Routing & Travel Time Estimation Tool — Phase 3
Calculates realistic walking and transit times between sequential stops in a day plan.
Uses Haversine distance with urban transit curves (walking under 1.5km, taxi/metro over 1.5km).
"""
from __future__ import annotations
import math
from app.models.schemas import Stop


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def calculate_sequential_transit_times(stops: list[Stop]) -> list[Stop]:
    """
    Given an ordered list of stops for a single day, calculates and assigns
    `travel_time_from_prev_minutes` for each stop (0 for the first stop).
    """
    if not stops:
        return []

    updated_stops: list[Stop] = []

    for i, stop in enumerate(stops):
        if i == 0:
            stop.travel_time_from_prev_minutes = 0
        else:
            prev = stops[i - 1]
            dist_km = haversine_distance_km(prev.lat, prev.lon, stop.lat, stop.lon)

            # Urban routing heuristic:
            # - Short distances (<= 1.2 km): Walking at 4.5 km/h
            # - Longer distances (> 1.2 km): Taxi/Metro at avg 25 km/h + 4 min buffer
            if dist_km <= 1.2:
                minutes = round((dist_km / 4.5) * 60)
            else:
                minutes = round(4 + (dist_km / 25.0) * 60)

            # Keep reasonable bounds (min 5 min, max 45 min)
            stop.travel_time_from_prev_minutes = max(5, min(minutes, 50))

        updated_stops.append(stop)

    return updated_stops
