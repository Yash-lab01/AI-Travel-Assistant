"""
iCalendar (.ics) Generator — Phase 7
Generates RFC 5545 compliant .ics calendar files for WanderAI itineraries.
Compatible with Google Calendar, Apple Calendar, Microsoft Outlook, and mobile calendar apps.
"""
from __future__ import annotations
from datetime import datetime, date, timedelta, time, timezone
import re
from typing import Optional

from app.models.schemas import Itinerary, DayPlan, Stop


def _escape_text(text: str) -> str:
    """Escape text for RFC 5545 format (semicolons, commas, backslashes, newlines)."""
    if not text:
        return ""
    text = text.replace('\\', '\\\\')
    text = text.replace(';', '\\;')
    text = text.replace(',', '\\,')
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '')
    return text


def _format_datetime(dt: datetime) -> str:
    """Format datetime as UTC iCalendar string (YYYYMMDDTHHMMSSZ)."""
    return dt.strftime("%Y%m%dT%H%M%SZ")


def generate_itinerary_ical(itinerary: Itinerary, start_date: Optional[date] = None) -> str:
    """
    Generate complete RFC 5545 .ics calendar content from an Itinerary object.
    """
    now = datetime.now(timezone.utc)
    dtstamp = _format_datetime(now)

    dest = itinerary.trip_request.destination if itinerary.trip_request else "Trip"
    
    # Determine base start date (tomorrow if not provided)
    if not start_date:
        if itinerary.trip_request and itinerary.trip_request.start_date:
            start_date = itinerary.trip_request.start_date
        else:
            start_date = date.today() + timedelta(days=1)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//WanderAI//Travel Planner//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:WanderAI — {dest} Itinerary",
        "X-WR-TIMEZONE:UTC",
    ]

    days: list[DayPlan] = itinerary.days or []

    for day_idx, day in enumerate(days):
        current_day_date = start_date + timedelta(days=day_idx)
        current_time = datetime.combine(current_day_date, time(9, 0))  # Morning 9:00 AM start

        stops: list[Stop] = day.stops or []
        for stop_idx, stop in enumerate(stops):
            # Account for transit time before this stop
            transit_min = stop.travel_time_from_prev_minutes or (0 if stop_idx == 0 else 15)
            if stop_idx > 0 and transit_min > 0:
                current_time += timedelta(minutes=transit_min)

            duration_min = stop.duration_minutes or 60
            start_dt = current_time
            end_dt = current_time + timedelta(minutes=duration_min)
            current_time = end_dt  # Move cursor to end of stop

            uid = f"{stop.id or stop_idx}-{day.day_number}-{itinerary.id[:8]}@wanderai.app"
            summary = f"{stop.name or 'Attraction'} — Day {day.day_number} ({stop.category.capitalize() if stop.category else 'Stop'})"
            
            desc_parts = []
            if stop.narration:
                desc_parts.append(f'"{stop.narration}"')
            elif stop.description:
                desc_parts.append(stop.description)
            
            desc_parts.append(f"\n⏱️ Duration: {duration_min} minutes")
            if stop.estimated_cost_usd is not None:
                desc_parts.append(f"💵 Est. Cost: ${stop.estimated_cost_usd:.2f} USD")
            if stop.is_niche:
                desc_parts.append("💎 Curated Community Hidden Gem")
            if stop.lat and stop.lon:
                nav_url = f"https://www.google.com/maps/dir/?api=1&destination={stop.lat},{stop.lon}&travelmode=walking"
                desc_parts.append(f"🗺️ Navigation: {nav_url}")
            desc_parts.append("\nCrafted by WanderAI Multi-Agent Travel Planner")

            location = stop.address or f"{stop.name}, {dest}"

            lines.append("BEGIN:VEVENT")
            lines.append(f"UID:{uid}")
            lines.append(f"DTSTAMP:{dtstamp}")
            lines.append(f"DTSTART:{_format_datetime(start_dt)}")
            lines.append(f"DTEND:{_format_datetime(end_dt)}")
            lines.append(f"SUMMARY:{_escape_text(summary)}")
            lines.append(f"DESCRIPTION:{_escape_text(' '.join(desc_parts))}")
            lines.append(f"LOCATION:{_escape_text(location)}")
            if stop.lat and stop.lon:
                lines.append(f"GEO:{stop.lat:.6f};{stop.lon:.6f}")
            lines.append("STATUS:CONFIRMED")
            lines.append("TRANSP:OPAQUE")
            lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
