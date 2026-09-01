"""
Smart Weather-Aware Packing List Generator — Phase 7
Generates customized, categorized travel packing checklists based on destination climate,
Open-Meteo weather forecasts, trip duration, electrical standard, and scheduled activities.
"""
from __future__ import annotations
import os
import json
import re
from typing import Optional, Any

from app.models.schemas import (
    Itinerary,
    PackingListResponse,
    PackingListCategory,
    PackingListItem,
)

GOOGLE_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")


def safe_extract_text(content: Any) -> str:
    """Safely extract string text from LLM response."""
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


PACKING_SYSTEM_PROMPT = """You are an expert travel packing strategist. Based on the trip destination, duration, weather forecast notes, and scheduled activities, generate a structured, comprehensive packing checklist tailored specifically to this journey.

Rules:
1. Provide 4-5 categories:
   - "clothing": Clothing & Footwear (adapt to duration, climate, and dress codes e.g. temple modesty, beachwear)
   - "weather": Weather Protection & Toiletries (sunscreen, umbrella/rain jacket, bug spray if tropical, lip balm)
   - "electronics": Tech, Adapters & Voltage (destination-specific plug types, power bank, charging cables)
   - "health_docs": Documents & Essentials (passport/ID, cash/forex card, basic meds)
   - "activity": Destination & Activity Gear (hiking footwear, quick-dry towel, dry bag, sunglasses)
2. Each item must have:
   - item: concise name (e.g. "Type C/D Power Adapter", "Breathable Linen Shirts (x3)")
   - category: one of ["clothing", "weather", "electronics", "health_docs", "activity"]
   - reason: brief rationale (e.g. "Required for historic temples in Rajasthan", "Open-Meteo indicates 60% chance of showers")
   - is_essential: boolean (true for critical must-haves, false for nice-to-haves)

Respond ONLY with valid JSON matching this exact structure:
{
  "weather_summary": "Brief 1-sentence weather overview for travelers",
  "categories": [
    {
      "name": "Clothing & Footwear",
      "icon": "👕",
      "items": [
        {"item": "...", "category": "clothing", "reason": "...", "is_essential": true}
      ]
    }
  ]
}"""


def _get_fallback_packing_list(destination: str, num_days: int, weather_note: str = "") -> PackingListResponse:
    """Heuristic fallback packing list when LLMs are unavailable."""
    is_tropical = any(k in destination.lower() for k in ["goa", "bali", "kerala", "phuket", "thailand", "mexico", "beach", "island"])
    
    categories = [
        PackingListCategory(
            name="Clothing & Footwear",
            icon="👕",
            items=[
                PackingListItem(item=f"{num_days + 1}x Breathable Day Outfits", category="clothing", reason=f"Priced for {num_days}-day itinerary with active walking", is_essential=True),
                PackingListItem(item="Comfortable Walking Shoes / Sneakers", category="clothing", reason="Essential for exploring city stops and heritage walks", is_essential=True),
                PackingListItem(item="Swimwear & Beach Towel" if is_tropical else "Light Jacket / Layering Piece", category="clothing", reason="Climate-appropriate outfit", is_essential=is_tropical),
                PackingListItem(item="Modest Attire (Covered shoulders/knees)", category="clothing", reason="Respectful dress for temples, churches, and heritage monuments", is_essential=True),
            ]
        ),
        PackingListCategory(
            name="Weather & Toiletries",
            icon="☀️",
            items=[
                PackingListItem(item="Broad Spectrum Sunscreen SPF 50+", category="weather", reason="Protection during outdoor exploration", is_essential=True),
                PackingListItem(item="Compact Travel Umbrella / Poncho", category="weather", reason="Preparedness for unexpected weather shifts", is_essential=True),
                PackingListItem(item="Insect Repellent & Hydrocortisone", category="weather", reason="Helpful for evening outdoor dining and coastal areas", is_essential=is_tropical),
                PackingListItem(item="Reusable Insulated Water Bottle", category="weather", reason="Stay hydrated across walking tours", is_essential=True),
            ]
        ),
        PackingListCategory(
            name="Tech & Power",
            icon="🔌",
            items=[
                PackingListItem(item="Universal Travel Power Adapter", category="electronics", reason="Ensures compatibility with local wall socket types", is_essential=True),
                PackingListItem(item="10,000mAh+ Power Bank", category="electronics", reason="Maintains phone battery for all-day navigation and photography", is_essential=True),
                PackingListItem(item="Offline Map / Itinerary PDF Downloaded", category="electronics", reason="Accessible even in areas with spotty roaming connectivity", is_essential=True),
            ]
        ),
        PackingListCategory(
            name="Documents & Essentials",
            icon="🛂",
            items=[
                PackingListItem(item="Government ID / Passport Copies", category="health_docs", reason="Required for hotel check-in and monument entry tickets", is_essential=True),
                PackingListItem(item="Local Currency Cash + Travel Forex Card", category="health_docs", reason="Useful for street food, local stalls, and auto/taxis", is_essential=True),
                PackingListItem(item="Personal First-Aid & Motion Sickness Meds", category="health_docs", reason="Basic travel wellness kit", is_essential=True),
            ]
        ),
    ]

    return PackingListResponse(
        destination=destination,
        weather_summary=weather_note or f"Expected pleasant conditions for {destination}.",
        categories=categories,
    )


async def generate_smart_packing_list(itinerary: Itinerary) -> PackingListResponse:
    """
    Generates a personalized packing list from an Itinerary object using LLM.
    """
    dest = itinerary.trip_request.destination if itinerary.trip_request else "Destination"
    days = itinerary.days or []
    num_days = len(days) if days else (itinerary.trip_request.num_days if itinerary.trip_request else 3)
    
    weather_notes = [d.weather_note for d in days if d.weather_note]
    combined_weather = " | ".join(weather_notes) if weather_notes else "Moderate climate."

    categories_present = set()
    for d in days:
        for s in (d.stops or []):
            if s.category:
                categories_present.add(s.category)
    
    activities_str = ", ".join(list(categories_present)[:8]) if categories_present else "General Sightseeing, Dining, Walks"

    user_context = (
        f"Destination: {dest}\n"
        f"Duration: {num_days} days\n"
        f"Weather Forecasts: {combined_weather}\n"
        f"Scheduled Activity Types: {activities_str}\n"
        f"Travel Style: {itinerary.trip_request.travel_style if itinerary.trip_request else 'balanced'}\n"
    )

    # 1. Try Gemini 2.5 Flash
    if GOOGLE_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=GOOGLE_KEY,
                temperature=0.3,
            )
            messages = [
                {"role": "system", "content": PACKING_SYSTEM_PROMPT},
                {"role": "user", "content": user_context},
            ]
            response = await llm.ainvoke(messages)
            raw = safe_extract_text(response.content)
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                cats = []
                for c in data.get("categories", []):
                    items = [
                        PackingListItem(
                            item=it.get("item", "Item"),
                            category=it.get("category", "clothing"),
                            reason=it.get("reason"),
                            is_essential=it.get("is_essential", True),
                        )
                        for it in c.get("items", [])
                    ]
                    if items:
                        cats.append(PackingListCategory(name=c.get("name", "Essentials"), icon=c.get("icon", "🎒"), items=items))
                
                if cats:
                    return PackingListResponse(
                        destination=dest,
                        weather_summary=data.get("weather_summary", combined_weather),
                        categories=cats,
                    )
        except Exception as e:
            print(f"[packing_list] Gemini packing generation failed: {e}")

    # 2. Try Groq Fallback
    if GROQ_KEY:
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(model="llama3-8b-8192", groq_api_key=GROQ_KEY, temperature=0.3)
            messages = [
                {"role": "system", "content": PACKING_SYSTEM_PROMPT},
                {"role": "user", "content": user_context},
            ]
            response = await llm.ainvoke(messages)
            raw = safe_extract_text(response.content)
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                cats = []
                for c in data.get("categories", []):
                    items = [
                        PackingListItem(
                            item=it.get("item", "Item"),
                            category=it.get("category", "clothing"),
                            reason=it.get("reason"),
                            is_essential=it.get("is_essential", True),
                        )
                        for it in c.get("items", [])
                    ]
                    if items:
                        cats.append(PackingListCategory(name=c.get("name", "Essentials"), icon=c.get("icon", "🎒"), items=items))
                
                if cats:
                    return PackingListResponse(
                        destination=dest,
                        weather_summary=data.get("weather_summary", combined_weather),
                        categories=cats,
                    )
        except Exception as e:
            print(f"[packing_list] Groq packing generation failed: {e}")

    # 3. Fallback
    return _get_fallback_packing_list(dest, num_days, combined_weather)
