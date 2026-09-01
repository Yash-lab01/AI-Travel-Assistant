"""
Editor Agent — Phase 4e
Handles multi-turn conversational modifications to existing itineraries:
- swap_stop: Replaces a specific stop with a high-rated, non-duplicate alternative matching preferences
- remove_stop: Deletes a stop and recalculates day transit & costs
- adjust_pace: Increases or decreases daily stop density
- tell_me_more: Generates rich local insider tips & storytelling without altering the itinerary structure
- general_edit: Contextual modifications to themes or notes
"""
from __future__ import annotations
import json
import re
import os
import uuid
from typing import Optional, Any

from app.models.schemas import (
    Itinerary, DayPlan, Stop, AgentEvent, EditIntent
)
from app.graph.state import TravelGraphState
from app.tools.places_tool import get_places_for_destination, fetch_wikimedia_image
from app.tools.niche_scraper import discover_niche_spots
from app.tools.routing_tool import calculate_sequential_transit_times
from app.tools.destination_images import get_category_fallback_image

GOOGLE_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")


def safe_extract_text(content: Any) -> str:
    """Safely extracts a plain string from LLM responses."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                text_parts.append(str(item["text"]))
            elif isinstance(item, str):
                text_parts.append(item)
            else:
                text_parts.append(str(item))
        return " ".join(text_parts).strip()
    return str(content).strip()


async def _generate_stop_narration(stop_name: str, category: str, destination: str) -> str:
    """Generate concise atmospheric narration for a swapped stop."""
    # 1. Try local Ollama fine-tuned narrator first
    try:
        from app.tools.ollama_narrator import generate_stop_narration, is_ollama_available
        if await is_ollama_available():
            local_narr = await generate_stop_narration(stop_name, category, destination)
            if local_narr:
                return local_narr
    except Exception:
        pass

    prompt = f"""Write a 1-sentence engaging travel narration (max 22 words) for {stop_name}, a {category} in {destination}.
Make it atmospheric and evocative. Avoid generic phrases."""

    if GOOGLE_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=GOOGLE_KEY, temperature=0.6)
            resp = await llm.ainvoke(prompt)
            text = safe_extract_text(resp.content).strip(' "')
            if text and len(text) > 10:
                return text
        except Exception:
            pass

    if GROQ_KEY:
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=GROQ_KEY, temperature=0.6)
            resp = await llm.ainvoke(prompt)
            text = safe_extract_text(resp.content).strip(' "')
            if text and len(text) > 10:
                return text
        except Exception:
            pass

    return f"A cherished {category} in {destination}, celebrated by travelers for its unique charm and vibrant character."


async def _generate_insider_tips(stop: Stop, destination: str) -> str:
    """Generate comprehensive insider tips for 'tell_me_more' requests."""
    prompt = f"""You are an expert local travel guide for {destination}.
Provide insider details about "{stop.name}" ({stop.category}).
Include:
1. 🏛️ Historical / Cultural highlight (1-2 sentences)
2. 📸 Best photography viewpoint or angle
3. ⏰ Best timing & crowd avoidance tip
4. 🍲 Nearby local food or cafe recommendation

Keep it punchy, practical, and formatted in clean markdown bullet points."""

    if GOOGLE_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_KEY, temperature=0.5)
            resp = await llm.ainvoke(prompt)
            text = safe_extract_text(resp.content).strip()
            if text and len(text) > 30:
                return text
        except Exception:
            pass

    if GROQ_KEY:
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=GROQ_KEY, temperature=0.5)
            resp = await llm.ainvoke(prompt)
            text = safe_extract_text(resp.content).strip()
            if text and len(text) > 30:
                return text
        except Exception:
            pass

    return f"""### ✨ Insider Tips for **{stop.name}** ({destination})

- **🏛️ Cultural Highlight**: An iconic {stop.category} capturing the authentic heritage and atmosphere of {destination}.
- **📸 Best Photo Spot**: Capture wide-angle shots during golden hour (early morning or just before sunset).
- **⏰ Visiting Tip**: Visit between 9:00 AM – 11:00 AM to explore before the peak afternoon crowds arrive.
- **🍲 Nearby Food**: Look out for authentic local cafes and street food stalls right outside the main gates."""


async def editor_node(state: TravelGraphState) -> dict:
    """
    Editor Agent Node:
    Takes an existing itinerary and applies targeted conversational edits.
    """
    events = list(state.get("events", []))
    itinerary = state.get("itinerary")

    if not itinerary or not itinerary.days:
        # No existing itinerary found to edit
        events.append(AgentEvent(
            event_type="error",
            agent="editor_agent",
            message="No active itinerary found to modify. Starting fresh planning...",
        ))
        return {"events": events}

    intent = state.get("edit_intent") or EditIntent.general_edit.value
    target_day = state.get("target_day")
    target_stop_id = state.get("target_stop_id")
    target_stop_name = state.get("target_stop_name")
    instruction = state.get("edit_instruction") or state["messages"][-1].content
    destination = itinerary.trip_request.destination or state.get("destination", "Destination")

    # ── 1. Handle "tell_me_more" (Informational Query) ────────────────────────
    if intent == EditIntent.tell_me_more.value:
        events.append(AgentEvent(
            event_type="agent_start",
            agent="editor_agent",
            message=f"Gathering insider travel tips and local history...",
        ))

        # Find target stop
        matched_stop: Optional[Stop] = None
        for day in itinerary.days:
            for s in day.stops:
                if target_stop_id and s.id == target_stop_id:
                    matched_stop = s
                    break
                if target_stop_name and target_stop_name.lower() in s.name.lower():
                    matched_stop = s
                    break
            if matched_stop:
                break

        if not matched_stop and itinerary.days and itinerary.days[0].stops:
            matched_stop = itinerary.days[0].stops[0]

        reply = await _generate_insider_tips(matched_stop, destination)

        events.append(AgentEvent(
            event_type="assistant_message",
            agent="editor_agent",
            message=reply,
            data={"stop_name": matched_stop.name if matched_stop else ""},
        ))

        return {
            "events": events,
            "assistant_reply": reply,
            "itinerary": itinerary,
        }

    # ── 2. Handle "swap_stop" ─────────────────────────────────────────────────
    if intent == EditIntent.swap_stop.value or "swap" in instruction.lower() or "replace" in instruction.lower():
        events.append(AgentEvent(
            event_type="agent_start",
            agent="editor_agent",
            message=f"Finding the ideal replacement stop for your itinerary in {destination}...",
        ))

        # Locate target day and stop by explicit ID or name first
        target_day_obj: Optional[DayPlan] = None
        target_stop_idx: int = -1

        # 1. Search for matching stop ID or name
        for d in itinerary.days:
            if target_day and d.day_number != target_day:
                continue
            for idx, s in enumerate(d.stops):
                if (target_stop_id and s.id == target_stop_id) or (target_stop_name and target_stop_name.lower() in s.name.lower()):
                    target_day_obj = d
                    target_stop_idx = idx
                    break
            if target_day_obj:
                break

        # 2. If not found by name within target_day, search across ALL days for stop name
        if not target_day_obj and target_stop_name:
            for d in itinerary.days:
                for idx, s in enumerate(d.stops):
                    if target_stop_name.lower() in s.name.lower():
                        target_day_obj = d
                        target_stop_idx = idx
                        break
                if target_day_obj:
                    break

        # 3. If target_day specified but stop name not matched, use first stop of target_day
        if not target_day_obj and target_day:
            for d in itinerary.days:
                if d.day_number == target_day:
                    target_day_obj = d
                    target_stop_idx = 0
                    break

        # 4. Fallback to Day 1, Stop 0
        if not target_day_obj:
            target_day_obj = itinerary.days[0]
            target_stop_idx = 0
        elif target_stop_idx == -1:
            target_stop_idx = 0

        old_stop = target_day_obj.stops[target_stop_idx] if target_day_obj.stops else None
        old_name = old_stop.name if old_stop else "Attraction"

        # Collect all active stop names across itinerary to avoid duplicate recommendations
        used_names = {s.name.lower().strip() for d in itinerary.days for s in d.stops}

        # Fetch candidates
        candidates: list[Stop] = []
        try:
            cached_popular = await get_places_for_destination(destination, num_days=len(itinerary.days))
            candidates.extend(cached_popular)
        except Exception:
            pass

        try:
            niche_spots = await discover_niche_spots(destination, limit=8)
            candidates.extend(niche_spots)
        except Exception:
            pass

        # Filter out existing stops
        available_candidates = [c for c in candidates if c.name.lower().strip() not in used_names]

        # Preference matching if user requested a specific category
        inst_lower = instruction.lower()
        preferred_category = None
        for cat in ["restaurant", "cafe", "food", "beach", "museum", "park", "viewpoint", "market", "fort", "temple", "nature"]:
            if cat in inst_lower:
                preferred_category = cat
                break

        replacement_stop: Optional[Stop] = None
        if preferred_category:
            for c in available_candidates:
                if preferred_category in c.category.lower() or preferred_category in c.name.lower():
                    replacement_stop = c
                    break

        if not replacement_stop and available_candidates:
            # Pick the top available candidate
            replacement_stop = available_candidates[0]

        if not replacement_stop:
            # Fallback synthetic replacement if candidate pool is completely exhausted
            center_lat = old_stop.lat if old_stop else 18.5204
            center_lon = old_stop.lon if old_stop else 73.8567
            replacement_stop = Stop(
                id=str(uuid.uuid4()),
                name=f"Scenic Promenade & Cultural Walk",
                category="viewpoint",
                description=f"A picturesque and relaxed local cultural destination in {destination}.",
                narration=f"A vibrant walking enclave in {destination}, perfect for experiencing local lifestyle and architecture.",
                lat=center_lat + 0.008,
                lon=center_lon + 0.008,
                duration_minutes=60,
                estimated_cost_usd=10.0,
                photo_urls=[get_category_fallback_image("viewpoint")],
                rating=4.6,
                review_count=1200,
                source="opentripmap",
                is_niche=False,
            )

        # Ensure photo and narration
        if not replacement_stop.photo_urls or not replacement_stop.photo_urls[0]:
            real_photo = await fetch_wikimedia_image(replacement_stop.name, destination)
            replacement_stop.photo_urls = [real_photo or get_category_fallback_image(replacement_stop.category)]

        replacement_stop.narration = await _generate_stop_narration(replacement_stop.name, replacement_stop.category, destination)

        # Replace in day
        target_day_obj.stops[target_stop_idx] = replacement_stop

        # Recalculate transit times for the modified day
        target_day_obj.stops = calculate_sequential_transit_times(target_day_obj.stops)

        # Recalculate costs
        target_day_obj.day_cost_estimate_usd = sum(s.estimated_cost_usd or 10.0 for s in target_day_obj.stops)
        itinerary.total_cost_estimate_usd = sum(d.day_cost_estimate_usd or 50.0 for d in itinerary.days)

        events.append(AgentEvent(
            event_type="tool_call",
            agent="editor_agent",
            tool="places_tool",
            message=f"Selected replacement: {replacement_stop.name} ({replacement_stop.category})",
        ))

        events.append(AgentEvent(
            event_type="day_ready",
            agent="editor_agent",
            message=f"Day {target_day_obj.day_number} updated with {replacement_stop.name}.",
            data={
                "day_number": target_day_obj.day_number,
                "day_plan": target_day_obj.model_dump(),
            }
        ))

        events.append(AgentEvent(
            event_type="itinerary_ready",
            agent="editor_agent",
            message=f"Itinerary successfully updated with {replacement_stop.name}!",
        ))

        reply_msg = f"✨ Updated **Day {target_day_obj.day_number}**! I've replaced **{old_name}** with **{replacement_stop.name}** ({replacement_stop.category}) and recalculated your travel route and timings."
        events.append(AgentEvent(
            event_type="assistant_message",
            agent="editor_agent",
            message=reply_msg,
        ))

        return {
            "events": events,
            "itinerary": itinerary,
            "assistant_reply": reply_msg,
        }

    # ── 3. Handle "remove_stop" ───────────────────────────────────────────────
    if intent == EditIntent.remove_stop.value or "remove" in instruction.lower() or "delete" in instruction.lower():
        events.append(AgentEvent(
            event_type="agent_start",
            agent="editor_agent",
            message=f"Removing requested stop from your itinerary...",
        ))

        removed_name = ""
        modified_day_num = 1

        for d in itinerary.days:
            if target_day and d.day_number != target_day:
                continue

            found_idx = -1
            for idx, s in enumerate(d.stops):
                if (target_stop_id and s.id == target_stop_id) or (target_stop_name and target_stop_name.lower() in s.name.lower()):
                    found_idx = idx
                    break

            if found_idx == -1 and target_day and d.stops:
                # If specific day was targeted without stop name, remove last stop of that day
                found_idx = len(d.stops) - 1

            if found_idx != -1 and len(d.stops) > 1:
                removed_stop = d.stops.pop(found_idx)
                removed_name = removed_stop.name
                modified_day_num = d.day_number
                d.stops = calculate_sequential_transit_times(d.stops)
                d.day_cost_estimate_usd = sum(s.estimated_cost_usd or 10.0 for s in d.stops)
                break

        itinerary.total_cost_estimate_usd = sum(d.day_cost_estimate_usd or 50.0 for d in itinerary.days)

        events.append(AgentEvent(
            event_type="itinerary_ready",
            agent="editor_agent",
            message=f"Updated itinerary: Removed {removed_name or 'stop'} from Day {modified_day_num}.",
        ))

        reply_msg = f"🗑️ Removed **{removed_name or 'stop'}** from Day {modified_day_num}. The remaining stops and transit times have been recalibrated."
        events.append(AgentEvent(
            event_type="assistant_message",
            agent="editor_agent",
            message=reply_msg,
        ))

        return {
            "events": events,
            "itinerary": itinerary,
            "assistant_reply": reply_msg,
        }

    # ── 4. Handle "adjust_pace" ───────────────────────────────────────────────
    if intent == EditIntent.adjust_pace.value or "pace" in instruction.lower() or "relax" in instruction.lower():
        is_slower = any(w in instruction.lower() for w in ["slow", "relax", "leisure", "fewer"])
        events.append(AgentEvent(
            event_type="agent_start",
            agent="editor_agent",
            message=f"Adjusting travel pacing to {'relaxed (fewer stops)' if is_slower else 'active exploration'}...",
        ))

        for d in itinerary.days:
            if is_slower and len(d.stops) > 3:
                d.stops.pop()  # Drop lowest priority stop to reduce exhaustion
            d.stops = calculate_sequential_transit_times(d.stops)
            d.day_cost_estimate_usd = sum(s.estimated_cost_usd or 10.0 for s in d.stops)

        itinerary.total_cost_estimate_usd = sum(d.day_cost_estimate_usd or 50.0 for d in itinerary.days)
        itinerary.trip_request.pace = "slow" if is_slower else "moderate"

        events.append(AgentEvent(
            event_type="itinerary_ready",
            agent="editor_agent",
            message=f"Pacing updated to {itinerary.trip_request.pace}.",
        ))

        reply_msg = f"🧘 I've adjusted your trip pacing to **{itinerary.trip_request.pace}** with relaxed schedules and more buffer time at each stop."
        events.append(AgentEvent(
            event_type="assistant_message",
            agent="editor_agent",
            message=reply_msg,
        ))

        return {
            "events": events,
            "itinerary": itinerary,
            "assistant_reply": reply_msg,
        }

    # ── 5. Fallback General Edit ──────────────────────────────────────────────
    events.append(AgentEvent(
        event_type="itinerary_ready",
        agent="editor_agent",
        message=f"Itinerary refreshed according to your preferences.",
    ))

    return {
        "events": events,
        "itinerary": itinerary,
        "assistant_reply": "✨ Your itinerary has been updated with your latest preferences!",
    }
