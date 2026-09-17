"""
Intake Agent — Phase 3
Extracts structured TripRequest from freeform messages using Gemini 3.5 Flash / Groq with robust regex fallback.
Includes conversational clarification logic: detects underspecified requests and generates
contextual clarifying questions with clickable chips, while preserving destination across turns.
"""
from __future__ import annotations
import json
import re
import os
from typing import Optional, Any

from langchain_core.messages import HumanMessage

from app.models.schemas import (
    TripRequest, TravelStyle, TravelPace, GroupType, AgentEvent,
    ClarificationQuestion, ClarificationOption, EditIntent
)
from app.graph.state import TravelGraphState

GOOGLE_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")

# ── Destination-Specific Clarification Templates ─────────────────────────────
DESTINATION_QUESTIONS: dict[str, list[dict]] = {
    "goa": [
        {
            "id": "goa_vibe",
            "question": "Which coastal atmospheres and regions would you like to experience?",
            "category": "region_vibe",
            "is_multi_select": True,
            "options": [
                {"label": "North Goa: Vibrant Beaches & Sunset Shacks", "value": "North Goa (beaches/nightlife)", "icon": "🌴"},
                {"label": "South Goa: Serene Coves & Heritage Villas", "value": "South Goa (heritage/relaxation)", "icon": "🏰"},
                {"label": "Panaji & Fontainhas: Portuguese Latin Quarter", "value": "Panaji Fontainhas Latin Quarter", "icon": "🏛️"},
                {"label": "Old Goa: Historic Cathedrals & Spice Plantations", "value": "Old Goa Cathedrals & Spice Plantations", "icon": "🌿"},
                {"label": "Mandovi & Chapora: River Cruises & Night Bazaars", "value": "Mandovi River Cruises & Bazaars", "icon": "⛵"},
            ]
        },
        {
            "id": "gem_focus",
            "question": "What travel style and activities appeal to you most?",
            "category": "travel_style",
            "is_multi_select": True,
            "options": [
                {"label": "Authentic Local Hidden Gems", "value": "niche", "icon": "💎"},
                {"label": "Iconic Forts & Coastal Viewpoints", "value": "popular", "icon": "🏛️"},
                {"label": "Seafood Shacks & Beachside Dining", "value": "foodie", "icon": "🍲"},
                {"label": "Water Sports, Kayaking & Surfing", "value": "adventure", "icon": "🏄"},
                {"label": "Sunset Lounges & Night Markets", "value": "relaxed", "icon": "🌅"},
            ]
        },
        {
            "id": "travel_pace",
            "question": "What daily sightseeing pace suits you best?",
            "category": "pace",
            "is_multi_select": False,
            "options": [
                {"label": "Relaxed & Leisurely (2-3 spots/day)", "value": "slow", "icon": "🧘"},
                {"label": "Balanced Exploration (4-5 stops/day)", "value": "moderate", "icon": "⚡"},
                {"label": "Packed Sightseeing (6+ spots/day)", "value": "fast", "icon": "🏃"},
            ]
        },
        {
            "id": "group_type",
            "question": "Who is traveling on this Goa trip?",
            "category": "group",
            "is_multi_select": False,
            "options": [
                {"label": "Solo Explorer", "value": "solo", "icon": "🎒"},
                {"label": "Couple / Romantic Getaway", "value": "couple", "icon": "💑"},
                {"label": "Family with Kids", "value": "family", "icon": "👨‍👩‍👧"},
                {"label": "Friends Group", "value": "friends", "icon": "👥"},
            ]
        }
    ],
    "mumbai": [
        {
            "id": "mumbai_vibe",
            "question": "What facets of Mumbai are you excited to explore?",
            "category": "travel_style",
            "is_multi_select": True,
            "options": [
                {"label": "Colonial Heritage & South Bombay Landmarks", "value": "cultural", "icon": "🏛️"},
                {"label": "Khau Galli Street Food & Heritage Cafes", "value": "foodie", "icon": "🍲"},
                {"label": "Kala Ghoda Art Enclaves & Hidden Bazaars", "value": "niche", "icon": "🎨"},
                {"label": "Marine Drive Promenades & Coastal Sunsets", "value": "relaxed", "icon": "🌅"},
                {"label": "Bollywood Heritage & Iconic Film Studios", "value": "popular", "icon": "🎬"},
            ]
        },
        {
            "id": "travel_pace",
            "question": "What daily sightseeing pace suits your trip?",
            "category": "pace",
            "is_multi_select": False,
            "options": [
                {"label": "Relaxed (2-3 spots/day)", "value": "slow", "icon": "🧘"},
                {"label": "Moderate Exploration (4-5 stops/day)", "value": "moderate", "icon": "⚡"},
                {"label": "Packed City Discovery (6+ stops/day)", "value": "fast", "icon": "🏃"},
            ]
        },
        {
            "id": "mumbai_highlights",
            "question": "Any signature experiences to prioritize?",
            "category": "interests",
            "is_multi_select": True,
            "options": [
                {"label": "Irani Chai, Bun Maska & Parsi Bakeries", "value": "irani_cafes", "icon": "☕"},
                {"label": "Elephanta Caves & Harbor Ferry", "value": "elephanta_caves", "icon": "🗿"},
                {"label": "Colaba Causeway & Crawford Market", "value": "bazaars", "icon": "🛍️"},
                {"label": "Seaside Marine Drive Golden Hour", "value": "coastal_walks", "icon": "🌊"},
            ]
        },
        {
            "id": "group_type",
            "question": "Who is traveling on this journey?",
            "category": "group",
            "is_multi_select": False,
            "options": [
                {"label": "Solo Explorer", "value": "solo", "icon": "🎒"},
                {"label": "Couple / Romantic", "value": "couple", "icon": "💑"},
                {"label": "Family", "value": "family", "icon": "👨‍👩‍👧"},
                {"label": "Friends Group", "value": "friends", "icon": "👥"},
            ]
        }
    ],
    "pune": [
        {
            "id": "pune_vibe",
            "question": "What would you like to explore in Pune?",
            "category": "travel_style",
            "is_multi_select": True,
            "options": [
                {"label": "Maratha Forts & Historic Peshwa Wadas", "value": "cultural", "icon": "🏰"},
                {"label": "Irani Cafes, Bakeries & Misal Trails", "value": "foodie", "icon": "☕"},
                {"label": "Sahyadri Hills, ARAI Vistas & Green Spots", "value": "niche", "icon": "🌿"},
                {"label": "Koregaon Park Cafes & Osho Gardens", "value": "relaxed", "icon": "🧘"},
                {"label": "Vibrant Peth Bazaars & Traditional Crafts", "value": "bazaars", "icon": "🛍️"},
            ]
        },
        {
            "id": "travel_pace",
            "question": "What daily pace would you prefer?",
            "category": "pace",
            "is_multi_select": False,
            "options": [
                {"label": "Relaxed (2-3 spots/day)", "value": "slow", "icon": "🧘"},
                {"label": "Moderate (4-5 stops/day)", "value": "moderate", "icon": "⚡"},
                {"label": "Active & Fast (6+ stops/day)", "value": "fast", "icon": "🏃"},
            ]
        },
        {
            "id": "pune_excursions",
            "question": "Any must-have Pune excursions?",
            "category": "interests",
            "is_multi_select": True,
            "options": [
                {"label": "Sinhagad Fort & Rural Pithla Bhakri", "value": "sinhagad_fort", "icon": "⛰️"},
                {"label": "Aga Khan Palace & Gandhi Memorial", "value": "aga_khan_palace", "icon": "🏛️"},
                {"label": "Pataleshwar Rock-Cut Cave Temple", "value": "pataleshwar_temple", "icon": "🗿"},
                {"label": "FC Road Student Cafes & Street Bites", "value": "street_food", "icon": "🍲"},
            ]
        },
        {
            "id": "group_type",
            "question": "Who are you traveling with?",
            "category": "group",
            "is_multi_select": False,
            "options": [
                {"label": "Solo Explorer", "value": "solo", "icon": "🎒"},
                {"label": "Couple", "value": "couple", "icon": "💑"},
                {"label": "Family", "value": "family", "icon": "👨‍👩‍👧"},
                {"label": "Friends", "value": "friends", "icon": "👥"},
            ]
        }
    ],
    "rajasthan": [
        {
            "id": "rajasthan_style",
            "question": "What is your primary focus for Rajasthan?",
            "category": "travel_style",
            "is_multi_select": True,
            "options": [
                {"label": "Majestic Royal Forts & Palaces", "value": "cultural", "icon": "👑"},
                {"label": "Ancient Stepwells & Desert Haveli Secrets", "value": "niche", "icon": "🏜️"},
                {"label": "Bazaars, Block Prints & Gem Markets", "value": "bazaars", "icon": "🛍️"},
                {"label": "Dal Baati Churma & Royal Rajasthani Feasts", "value": "foodie", "icon": "🍲"},
                {"label": "Desert Dunes & Sunset Folk Evenings", "value": "scenic", "icon": "🌅"},
            ]
        },
        {
            "id": "travel_pace",
            "question": "What sightseeing pace suits your royal tour?",
            "category": "pace",
            "is_multi_select": False,
            "options": [
                {"label": "Relaxed & Unhurried (2-3 stops/day)", "value": "slow", "icon": "🧘"},
                {"label": "Comprehensive Exploration (4-5 stops/day)", "value": "moderate", "icon": "⚡"},
                {"label": "High-Energy Tour (6+ stops/day)", "value": "fast", "icon": "🏃"},
            ]
        },
        {
            "id": "rajasthan_activities",
            "question": "Which signature experiences appeal to you?",
            "category": "interests",
            "is_multi_select": True,
            "options": [
                {"label": "Photography at Sunset Fort Miradors", "value": "photo_spots", "icon": "📸"},
                {"label": "Lake Pichola or Jal Mahal Water Vistas", "value": "water_vistas", "icon": "⛵"},
                {"label": "Local Textile & Blue Pottery Workshops", "value": "artisan_crafts", "icon": "🎨"},
                {"label": "Heritage Walking Trails in Walled Old Cities", "value": "heritage_walks", "icon": "🚶"},
            ]
        },
        {
            "id": "group_type",
            "question": "Travel party style?",
            "category": "group",
            "is_multi_select": False,
            "options": [
                {"label": "Solo Explorer", "value": "solo", "icon": "🎒"},
                {"label": "Couple / Romantic", "value": "couple", "icon": "💑"},
                {"label": "Family", "value": "family", "icon": "👨‍👩‍👧"},
                {"label": "Friends", "value": "friends", "icon": "👥"},
            ]
        }
    ],
    "kashmir": [
        {
            "id": "kashmir_style",
            "question": "What experiences are you dreaming of in Kashmir?",
            "category": "travel_style",
            "is_multi_select": True,
            "options": [
                {"label": "Dal Lake Shikara Rides & Serene Houseboats", "value": "scenic", "icon": "⛵"},
                {"label": "Mughal Terraced Gardens & Pari Mahal", "value": "cultural", "icon": "🌺"},
                {"label": "Snow Peaks & High-Altitude Gondola in Gulmarg", "value": "adventure", "icon": "❄️"},
                {"label": "Pine Forests, Valleys & Rivers of Pahalgam", "value": "niche", "icon": "🌲"},
                {"label": "Authentic Wazwan Feasts & Artisan Bazaars", "value": "foodie", "icon": "🍲"},
            ]
        },
        {
            "id": "travel_pace",
            "question": "What pace feels best amidst the valleys?",
            "category": "pace",
            "is_multi_select": False,
            "options": [
                {"label": "Relaxed & Peaceful (2-3 spots/day)", "value": "slow", "icon": "🧘"},
                {"label": "Moderate Valley Exploration (4-5 stops/day)", "value": "moderate", "icon": "⚡"},
                {"label": "Active Valley Trekking (5-6 spots/day)", "value": "fast", "icon": "🏃"},
            ]
        },
        {
            "id": "kashmir_highlights",
            "question": "Must-have valley highlights?",
            "category": "interests",
            "is_multi_select": True,
            "options": [
                {"label": "Sunrise Floating Vegetable Market on Dal Lake", "value": "floating_market", "icon": "🌅"},
                {"label": "Saffron Fields & Pampore Walnut Orchards", "value": "saffron_fields", "icon": "🌿"},
                {"label": "Old Srinagar Wooden Bridges & Historic Mosques", "value": "old_srinagar", "icon": "🏛️"},
                {"label": "Traditional Kashmiri Kahwa & Bakery Trail", "value": "kahwa_trail", "icon": "☕"},
            ]
        },
        {
            "id": "group_type",
            "question": "Who is joining this journey?",
            "category": "group",
            "is_multi_select": False,
            "options": [
                {"label": "Solo Explorer", "value": "solo", "icon": "🎒"},
                {"label": "Couple / Romantic Getaway", "value": "couple", "icon": "💑"},
                {"label": "Family", "value": "family", "icon": "👨‍👩‍👧"},
                {"label": "Friends Group", "value": "friends", "icon": "👥"},
            ]
        }
    ],
    "lisbon": [
        {
            "id": "lisbon_vibe",
            "question": "What atmosphere are you most excited to experience in Lisbon?",
            "category": "travel_style",
            "is_multi_select": True,
            "options": [
                {"label": "Historic Castles, Miradouros & Vintage Tram 28", "value": "cultural", "icon": "🏰"},
                {"label": "Pastéis de Nata, Port Wine & Intimate Fado Nights", "value": "foodie", "icon": "🍷"},
                {"label": "Secret Alleys & Flea Markets of Alfama", "value": "niche", "icon": "💎"},
                {"label": "Waterfront Belém & Monumental Architecture", "value": "popular", "icon": "⛵"},
                {"label": "Tile Museums, Contemporary Art & Mirador Lounges", "value": "relaxed", "icon": "🎨"},
            ]
        },
        {
            "id": "travel_pace",
            "question": "What daily pace suits your trip?",
            "category": "pace",
            "is_multi_select": False,
            "options": [
                {"label": "Relaxed Morning & Afternoon (2-3 stops/day)", "value": "slow", "icon": "☕"},
                {"label": "Comprehensive Day Exploration (4-5 stops/day)", "value": "moderate", "icon": "🚶"},
                {"label": "Packed City Discovery (6+ stops/day)", "value": "fast", "icon": "🏃"},
            ]
        },
        {
            "id": "lisbon_interests",
            "question": "Any special Lisbon highlights?",
            "category": "interests",
            "is_multi_select": True,
            "options": [
                {"label": "Sunset Drinks at Scenic Miradouro Vistas", "value": "sunset_miradouros", "icon": "🌅"},
                {"label": "Sintra Day Trip / Fairy-Tale Castles", "value": "sintra_trip", "icon": "🏰"},
                {"label": "Feira da Ladra Flea Market & Azulejo Tiles", "value": "flea_market", "icon": "🛍️"},
                {"label": "Fresh Atlantic Seafood & Petiscos Taverns", "value": "seafood_taverns", "icon": "🍤"},
            ]
        },
        {
            "id": "group_type",
            "question": "Who is traveling?",
            "category": "group",
            "is_multi_select": False,
            "options": [
                {"label": "Solo Traveler", "value": "solo", "icon": "🎒"},
                {"label": "Couple", "value": "couple", "icon": "💑"},
                {"label": "Family", "value": "family", "icon": "👨‍👩‍👧"},
                {"label": "Friends Group", "value": "friends", "icon": "👥"},
            ]
        }
    ]
}


def _get_generic_clarification_questions(destination: str) -> list[ClarificationQuestion]:
    """Fallback static clarifying questions — covers all 4 strategic dimensions with 4-5 options."""
    raw_qs = [
        {
            "id": "travel_style",
            "question": f"What type of experience are you looking for in {destination}?",
            "category": "travel_style",
            "is_multi_select": True,
            "options": [
                {"label": "Curated Iconic Landmarks & Must-See Sights", "value": "popular", "icon": "🏛️"},
                {"label": "Off-The-Beaten-Path Secrets & Hidden Gems", "value": "niche", "icon": "💎"},
                {"label": "Food, Local Cafes & Culinary Trails", "value": "foodie", "icon": "🍲"},
                {"label": "Scenic Nature, Parks & Viewpoints", "value": "adventure", "icon": "🌿"},
                {"label": "Art, Architecture & Cultural Heritage", "value": "cultural", "icon": "🎨"},
            ]
        },
        {
            "id": "travel_pace",
            "question": "What daily sightseeing pace suits your rhythm?",
            "category": "pace",
            "is_multi_select": False,
            "options": [
                {"label": "Relaxed & Leisurely (2-3 stops/day)", "value": "slow", "icon": "🧘"},
                {"label": "Balanced & Steady (4-5 stops/day)", "value": "moderate", "icon": "⚡"},
                {"label": "Packed & Energetic (6+ stops/day)", "value": "fast", "icon": "🏃"},
            ]
        },
        {
            "id": "interests",
            "question": "Which specific highlights are on your wishlist?",
            "category": "interests",
            "is_multi_select": True,
            "options": [
                {"label": "Golden Hour & Scenic Photo Spots", "value": "photo_spots", "icon": "📸"},
                {"label": "Boutique Cafes & Street Food Markets", "value": "cafes_markets", "icon": "☕"},
                {"label": "Historic Neighborhood Walking Tours", "value": "heritage_walks", "icon": "🚶"},
                {"label": "Sunset Viewpoints & Waterfront Panoramas", "value": "sunset_vistas", "icon": "🌅"},
                {"label": "Evening Dining, Music & Nightlife", "value": "nightlife", "icon": "🍷"},
            ]
        },
        {
            "id": "group_type",
            "question": "Who is traveling on this journey?",
            "category": "group",
            "is_multi_select": False,
            "options": [
                {"label": "Solo Explorer", "value": "solo", "icon": "🎒"},
                {"label": "Couple / Romantic", "value": "couple", "icon": "💑"},
                {"label": "Family with Kids", "value": "family", "icon": "👨‍👩‍👧"},
                {"label": "Friends Group", "value": "friends", "icon": "👥"},
            ]
        }
    ]
    return [
        ClarificationQuestion(
            id=q["id"],
            question=q["question"],
            category=q["category"],
            is_multi_select=q.get("is_multi_select", False),
            options=[ClarificationOption(**opt) for opt in q["options"]]
        )
        for q in raw_qs
    ]


# ── LLM-powered contextual clarification question generator ─────────────────
CLARIFICATION_SYSTEM_PROMPT = """You are an expert travel intake assistant. Based on the user's travel request and missing key dimensions, generate 3-4 strategic clarification questions with 4-5 rich, specific chip options each.

Dimensions to strategically retrieve if missing:
1. Travel Style & Vibe (set "is_multi_select": true) — Tailor options specifically to what is unique about {destination} (e.g. food, history, nightlife, nature, hidden gems).
2. Pacing (set "is_multi_select": false) — Daily stop volume (slow 2-3 stops, moderate 4-5 stops, packed 6+ stops).
3. Must-Have Activities / Interests (set "is_multi_select": true) — Specific local activities (e.g. photo spots, markets, culinary tastings, scenic walks, boat rides).
4. Group Type or Budget Tier (set "is_multi_select": false) — Solo, couple, family, friends or budget, mid-range, luxury.

Rules:
- Generate 3 to 4 questions.
- For multi-select questions (style, activities, vibes), provide 4 to 5 enticing, destination-tailored options.
- Each option needs:
  - "label": 2 to 5 words, evocative, specific to {destination} (avoid generic labels like "Culture").
  - "value": short identifier string.
  - "icon": single relevant emoji.
- Never repeat options.

Respond ONLY with valid JSON matching this exact schema:
{
  "questions": [
    {
      "id": "string (snake_case)",
      "question": "string",
      "category": "string (travel_style|pace|region_vibe|interests|group|budget)",
      "is_multi_select": boolean,
      "options": [
        {"label": "string", "value": "string", "icon": "emoji"}
      ]
    }
  ]
}"""


async def _generate_dynamic_clarification_questions(
    user_message: str,
    destination: str,
    num_days: int,
    missing_dimensions: Optional[list[str]] = None,
) -> list[ClarificationQuestion]:
    """Use LLM to generate contextual clarification questions based on the specific user prompt."""
    missing_str = f"Missing key dimensions to prioritize: {', '.join(missing_dimensions)}." if missing_dimensions else ""
    user_context = f"User request: '{user_message}'\nDestination: {destination}\nDuration: {num_days} days\n{missing_str}".strip()

    # Try Gemini first (fast, high quality)
    if GOOGLE_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-3.6-flash",
                google_api_key=GOOGLE_KEY,
                temperature=0.4,
            )
            messages = [
                {"role": "system", "content": CLARIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_context},
            ]
            response = await llm.ainvoke(messages)
            raw = safe_extract_text(response.content)
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                questions = [
                    ClarificationQuestion(
                        id=q["id"],
                        question=q["question"],
                        category=q["category"],
                        is_multi_select=bool(q.get("is_multi_select", False)),
                        options=[ClarificationOption(**opt) for opt in q["options"]]
                    )
                    for q in data.get("questions", [])
                ]
                if questions:
                    return questions
        except Exception as e:
            print(f"[intake] Dynamic clarification (Gemini) failed: {e}")

    # Try Groq fallback
    if GROQ_KEY:
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(model="openai/gpt-oss-20b", groq_api_key=GROQ_KEY, temperature=0.4)
            messages = [
                {"role": "system", "content": CLARIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_context},
            ]
            response = await llm.ainvoke(messages)
            raw = safe_extract_text(response.content)
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                questions = [
                    ClarificationQuestion(
                        id=q["id"],
                        question=q["question"],
                        category=q["category"],
                        is_multi_select=bool(q.get("is_multi_select", False)),
                        options=[ClarificationOption(**opt) for opt in q["options"]]
                    )
                    for q in data.get("questions", [])
                ]
                if questions:
                    return questions
        except Exception as e:
            print(f"[intake] Dynamic clarification (Groq) failed: {e}")

    # Final fallback: static generic questions
    print(f"[intake] Falling back to generic clarification questions for {destination}")
    return _get_generic_clarification_questions(destination)


# ── Slot extraction with LLM ────────────────────────────────────────────────
INTAKE_SYSTEM_PROMPT = """You are an expert travel intake agent. Convert the user's travel request into a structured JSON object.
Extract:
- destination: string (required, city/region/country name. Never return 'Unknown' if a city like Pune, Mumbai, Goa is mentioned)
- num_days: integer (1-14, default 3 if not specified)
- budget_usd: float or null
- niche_weight: float (0.0 to 1.0, default 0.5)
- travel_style: one of ["popular", "balanced", "niche", "cultural", "adventure", "foodie", "relaxed"]
- pace: one of ["slow", "moderate", "fast"]
- group_type: one of ["solo", "couple", "family", "friends"]
- interests: array of strings

Respond ONLY with valid JSON. No markdown, no explanation."""


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


async def _extract_with_llm(text: str) -> Optional[dict]:
    # 1. Try Gemini 2.5 Flash first (latest stable, high rate limit)
    if GOOGLE_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-3.6-flash",
                google_api_key=GOOGLE_KEY,
                temperature=0.0,
            )
            messages = [
                {"role": "system", "content": INTAKE_SYSTEM_PROMPT},
                {"role": "user",   "content": text},
            ]
            response = await llm.ainvoke(messages)
            raw = safe_extract_text(response.content)
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                if data.get("destination") and data["destination"].lower() != "unknown":
                    return data
        except Exception as e:
            print(f"[intake_agent] Gemini extraction failed: {e}")

    # 2. Try Groq (gpt-oss-20b)
    if GROQ_KEY:
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(
                model="openai/gpt-oss-20b",
                api_key=GROQ_KEY,
                temperature=0.0,
            )
            messages = [
                {"role": "system", "content": INTAKE_SYSTEM_PROMPT},
                {"role": "user",   "content": text},
            ]
            response = await llm.ainvoke(messages)
            raw = safe_extract_text(response.content)
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                if data.get("destination") and data["destination"].lower() != "unknown":
                    return data
        except Exception as e:
            print(f"[intake_agent] Groq extraction failed: {e}")


    return None


def _extract_with_regex(text: str) -> dict:
    """Robust rule-based parser for city, duration, budget, style."""
    text_lower = text.lower().strip()

    # Destination parsing
    destination = "Unknown"
    for prep in ["in ", "to ", "for ", "around ", "visit ", "explore "]:
        if prep in text_lower:
            parts = text_lower.split(prep, 1)
            candidate = parts[1].split(",")[0].split()[0].strip(".,!?").title()
            if candidate and candidate.lower() not in [
                "a", "the", "my", "our", "some", "trip", "days", "standard", "preferences", "defaults",
                "holiday", "vacation", "getaway", "tour", "itinerary", "somewhere", "anywhere", "break"
            ]:
                destination = candidate
                break

    # If destination is still Unknown, check if the first or last word is a known city/place
    if destination == "Unknown":
        words = [w.strip(".,!?") for w in text.split()]
        common_stops = {
            "3", "4", "5", "2", "1", "days", "day", "trip", "in", "to", "plan", "with", "submit", "preferences",
            "holiday", "vacation", "getaway", "tour", "itinerary", "somewhere", "anywhere", "travel", "places", "explore",
            "vacations", "holidays", "trips", "weekend", "week", "break"
        }
        candidates = [w.title() for w in words if w.lower() not in common_stops and len(w) > 2]
        if candidates:
            destination = candidates[0]

    # Number of days
    num_days = 3
    day_match = re.search(r'(\d+)\s*(?:day|night)', text_lower)
    if day_match:
        num_days = int(day_match.group(1))
    elif "weekend" in text_lower:
        num_days = 2
    elif "week" in text_lower:
        num_days = 7

    # Budget
    budget_usd = None
    budget_match = re.search(r'[\$€£](\d[\d,]*)|\b(\d[\d,]*)\s*(?:usd|dollars|euro|inr|rs|bucks|rupees)\b', text_lower)
    if budget_match:
        raw_val = budget_match.group(1) or budget_match.group(2)
        try:
            budget_usd = float(raw_val.replace(",", ""))
        except ValueError:
            pass

    # Travel style & Niche weight
    travel_style = "balanced"
    niche_weight = 0.5
    if any(w in text_lower for w in ["hidden gem", "offbeat", "secret", "local", "niche", "authentic"]):
        travel_style = "niche"
        niche_weight = 0.75
    elif any(w in text_lower for w in ["iconic", "must see", "tourist", "famous", "landmark"]):
        travel_style = "popular"
        niche_weight = 0.2
    elif any(w in text_lower for w in ["food", "foodie", "eat", "cafe", "restaurant"]):
        travel_style = "foodie"
    elif any(w in text_lower for w in ["culture", "history", "museum", "temple", "palace", "wada", "fort"]):
        travel_style = "cultural"

    # Group type
    group_type = "solo"
    if "couple" in text_lower or "honeymoon" in text_lower or "partner" in text_lower:
        group_type = "couple"
    elif "family" in text_lower or "kids" in text_lower:
        group_type = "family"
    elif "friends" in text_lower or "group" in text_lower:
        group_type = "friends"

    # Pace
    pace = "moderate"
    if any(w in text_lower for w in ["slow", "relaxed", "leisurely", "easy"]):
        pace = "slow"
    elif any(w in text_lower for w in ["fast", "packed", "full", "intensive", "busy"]):
        pace = "fast"

    return {
        "destination":    destination,
        "num_days":       num_days,
        "budget_usd":     budget_usd,
        "niche_weight":   niche_weight,
        "travel_style":   travel_style,
        "pace":           pace,
        "group_type":     group_type,
        "interests":      [],
    }


def _dict_to_trip_request(data: dict, raw_message: str) -> TripRequest:
    return TripRequest(
        destination=str(data.get("destination", "Unknown")).strip() or "Unknown",
        num_days=max(1, min(int(data.get("num_days", 3)), 14)),
        budget_usd=float(data["budget_usd"]) if data.get("budget_usd") else None,
        niche_weight=max(0.0, min(float(data.get("niche_weight", 0.5)), 1.0)),
        travel_style=_safe_enum(TravelStyle, data.get("travel_style", "balanced"), TravelStyle.balanced),
        pace=_safe_enum(TravelPace, data.get("pace", "moderate"), TravelPace.moderate),
        group_type=_safe_enum(GroupType, data.get("group_type", "solo"), GroupType.solo),
        interests=list(data.get("interests", [])),
        raw_message=raw_message,
    )


def classify_edit_intent(message: str, current_itinerary: Optional[Itinerary] = None) -> dict:
    """Classifies follow-up message intent when an itinerary already exists."""
    msg_l = message.lower().strip()

    # Check for day match (e.g. Day 1, Day 2)
    day_match = re.search(r'day\s*(\d+)', msg_l)
    target_day = int(day_match.group(1)) if day_match else None

    # Check for stop name match in current itinerary
    matched_stop = None
    if current_itinerary and current_itinerary.days:
        for d in current_itinerary.days:
            for s in d.stops:
                if s.name and len(s.name) >= 3 and s.name.lower() in msg_l:
                    matched_stop = s.name
                    if not target_day:
                        target_day = d.day_number
                    break
            if matched_stop:
                break

    # 1. New trip intent (e.g. "Plan 4 days in Tokyo", "Plan a new 3 day trip to Tokyo", "Take me to Paris instead")
    if re.search(r'\b(new trip|plan\s+(?:a\s+)?(?:new\s+)?(?:\d+\s+days?\s+)?trip|plan\s+\d+\s+days?\s+(?:in|to)|take me to|fly to|explore a new destination)\b', msg_l) and not any(k in msg_l for k in ['swap', 'replace', 'remove', 'delete', 'change', 'tell me']):
        return {"intent": EditIntent.new_trip.value, "target_day": None, "target_stop_name": None}

    # 2. Swap / Replace stop
    if re.search(r'\b(swap|replace|switch|different spot|alternative for|change stop)\b', msg_l):
        return {"intent": EditIntent.swap_stop.value, "target_day": target_day, "target_stop_name": matched_stop}

    # 3. Remove / Delete stop
    if re.search(r'\b(remove|delete|drop|cut|omit|skip)\b', msg_l):
        return {"intent": EditIntent.remove_stop.value, "target_day": target_day, "target_stop_name": matched_stop}

    # 4. Tell me more / Informational
    if re.search(r'\b(tell me more|more info|details about|story behind|history of|tips for|insider tips|what should i know|photo spot|guide for)\b', msg_l):
        return {"intent": EditIntent.tell_me_more.value, "target_day": target_day, "target_stop_name": matched_stop}

    # 5. Adjust pace
    if re.search(r'\b(pace|slow|relax|fast|intense|fewer stops|more stops|packed|exhausting|leisure)\b', msg_l):
        return {"intent": EditIntent.adjust_pace.value, "target_day": target_day, "target_stop_name": matched_stop}

    # 6. Change budget
    if re.search(r'\b(budget|cheaper|luxury|expensive|cost|money)\b', msg_l):
        return {"intent": EditIntent.change_budget.value, "target_day": target_day, "target_stop_name": matched_stop}

    return {"intent": EditIntent.general_edit.value, "target_day": target_day, "target_stop_name": matched_stop}


def _safe_enum(enum_class, value: str, default):
    try:
        return enum_class(value)
    except (ValueError, KeyError):
        return default


async def intake_node(state: TravelGraphState) -> dict:
    """
    Intake LangGraph node:
    1. Detects if this is a multi-turn edit to an existing itinerary vs a fresh trip plan.
    2. Extracts slots from user message (with fallback to previous turn or explicit state).
    3. Incorporates any user-selected clarification answers.
    4. If prompt is minimal and force_plan is False -> asks clarifying questions with chips.
    5. Otherwise -> proceeds to Ranker/Planner or Editor.
    """
    events = list(state.get("events", []))
    messages = state["messages"]
    last_user_msg = messages[-1].content if messages else "Trip to Goa"

    force_plan = state.get("force_plan", False)
    answers = state.get("clarification_answers") or {}
    explicit_dest = state.get("destination")
    explicit_days = state.get("num_days")
    existing_itinerary = state.get("itinerary")
    is_edit_session = state.get("is_edit", False) or existing_itinerary is not None

    # ── Check for Multi-Turn Edit ─────────────────────────────────────────────
    if is_edit_session and existing_itinerary and not answers and not force_plan:
        edit_meta = classify_edit_intent(last_user_msg, existing_itinerary)
        intent = edit_meta["intent"]

        if intent != EditIntent.new_trip.value:
            events.append(AgentEvent(
                event_type="agent_start",
                agent="intake_agent",
                message=f"Detected edit request ({intent.replace('_', ' ')}). Routing to Editor Agent...",
            ))
            return {
                "is_edit": True,
                "edit_intent": intent,
                "target_day": state.get("target_day") or edit_meta["target_day"],
                "target_stop_id": state.get("target_stop_id"),
                "target_stop_name": state.get("target_stop_name") or edit_meta["target_stop_name"],
                "edit_instruction": last_user_msg,
                "needs_clarification": False,
                "events": events,
            }

    events.append(AgentEvent(
        event_type="agent_start",
        agent="intake_agent",
        message="Analyzing your destination, duration, and travel preferences...",
    ))

    # Try LLM extraction first, fall back to regex
    extracted = await _extract_with_llm(last_user_msg)
    if not extracted:
        extracted = _extract_with_regex(last_user_msg)

    # If explicit destination/days passed in state, prioritize them
    if explicit_dest and explicit_dest.lower() != "unknown":
        extracted["destination"] = explicit_dest
    if explicit_days:
        extracted["num_days"] = explicit_days

    # If destination is still Unknown, check if previous trip_request has it
    if extracted.get("destination") == "Unknown" and state.get("trip_request"):
        prev_trip = state["trip_request"]
        if prev_trip.destination and prev_trip.destination != "Unknown":
            extracted["destination"] = prev_trip.destination
            extracted["num_days"] = prev_trip.num_days

    # Merge explicit clarification answers if user clicked chips (supports multi-select)
    if answers:
        def _to_list(val) -> list[str]:
            if isinstance(val, list):
                return [str(v).strip() for v in val if str(v).strip()]
            if isinstance(val, str) and val.strip():
                return [v.strip() for v in val.split(",") if v.strip()]
            return []

        # 1. Travel style & niche weighting
        if "travel_style" in answers:
            styles = _to_list(answers["travel_style"])
            if styles:
                if "niche" in styles and "popular" in styles:
                    extracted["niche_weight"] = 0.5
                    extracted["travel_style"] = "balanced"
                elif "niche" in styles:
                    extracted["niche_weight"] = 0.8
                    extracted["travel_style"] = "niche"
                elif "popular" in styles:
                    extracted["niche_weight"] = 0.2
                    extracted["travel_style"] = "popular"
                else:
                    known = {"cultural", "foodie", "adventure", "relaxed", "balanced"}
                    chosen = next((s for s in styles if s in known), styles[0])
                    extracted["travel_style"] = chosen

                current_interests = set(extracted.get("interests") or [])
                for s in styles:
                    current_interests.add(s)
                extracted["interests"] = list(current_interests)

        # 2. Pacing
        if "pace" in answers:
            paces = _to_list(answers["pace"])
            if paces:
                extracted["pace"] = paces[0]

        # 3. Regional / Vibe preference
        if "region_vibe" in answers:
            vibes = _to_list(answers["region_vibe"])
            if vibes:
                extracted["region_preference"] = " & ".join(vibes)

        # 4. Activities / Interests
        for interest_key in ["interests", "activity", "food", "gem_focus"]:
            if interest_key in answers:
                items = _to_list(answers[interest_key])
                if items:
                    current_interests = set(extracted.get("interests") or [])
                    current_interests.update(items)
                    extracted["interests"] = list(current_interests)

        # 5. Dietary preferences
        if "dietary" in answers:
            diet_items = _to_list(answers["dietary"])
            if diet_items:
                current_interests = set(extracted.get("interests") or [])
                for d in diet_items:
                    current_interests.add(f"{d} food")
                extracted["interests"] = list(current_interests)

        # 6. Group type
        if "group" in answers:
            groups = _to_list(answers["group"])
            if groups:
                g_val = groups[0].lower()
                if "couple" in g_val or "romantic" in g_val:
                    extracted["group_type"] = "couple"
                elif "family" in g_val or "kid" in g_val:
                    extracted["group_type"] = "family"
                elif "friend" in g_val:
                    extracted["group_type"] = "friends"
                else:
                    extracted["group_type"] = "solo"

        # 7. Budget tier
        if "budget" in answers:
            b_vals = _to_list(answers["budget"])
            if b_vals:
                b_val = b_vals[0].lower()
                if "budget" in b_val or "cheap" in b_val or "economy" in b_val:
                    extracted["budget_usd"] = 400.0
                elif "luxury" in b_val or "premium" in b_val or "high" in b_val:
                    extracted["budget_usd"] = 2500.0
                elif "moderate" in b_val or "mid" in b_val:
                    extracted["budget_usd"] = 1000.0

        # 8. Duration / Days
        if "duration" in answers or "num_days" in answers:
            d_vals = _to_list(answers.get("duration") or answers.get("num_days"))
            if d_vals:
                match = re.search(r'\d+', d_vals[0])
                if match:
                    extracted["num_days"] = int(match.group(0))

        # 9. Destination selection
        if "destination" in answers:
            dest_vals = _to_list(answers["destination"])
            if dest_vals:
                extracted["destination"] = dest_vals[0]

    trip_request = _dict_to_trip_request(extracted, raw_message=last_user_msg)
    if "region_preference" in extracted:
        trip_request.region_preference = extracted["region_preference"]

    # ── Strategic Fixed-Info Dimension Tracking (Phase 11D) ───────────────
    # Key fixed dimensions: destination, duration, travel style/interests, pace, group, budget
    msg_lower = last_user_msg.lower()
    has_explicit_dest = trip_request.destination != "Unknown"
    has_explicit_duration = (
        bool(re.search(r'\b(\d+)\s*(?:day|night)', msg_lower))
        or "weekend" in msg_lower
        or "week" in msg_lower
        or explicit_days is not None
    )
    has_explicit_style = (
        trip_request.travel_style != TravelStyle.balanced
        or bool(trip_request.interests)
        or any(w in msg_lower for w in ["hidden gem", "offbeat", "secret", "local", "niche", "authentic", "iconic", "famous", "landmark", "food", "foodie", "culture", "history", "museum", "adventure", "beach", "nature", "scenic"])
    )
    has_explicit_pace = any(w in msg_lower for w in ["slow", "relaxed", "leisure", "moderate", "fast", "packed", "busy", "intense", "stops/day"])
    has_explicit_group = any(w in msg_lower for w in ["solo", "couple", "honeymoon", "partner", "wife", "husband", "family", "kids", "children", "friend", "friends", "group", "colleagues"])
    has_explicit_budget = trip_request.budget_usd is not None or any(w in msg_lower for w in ["budget", "cheap", "luxury", "expensive", "mid-range", "economy", "$", "€", "£", "₹", "rs", "inr"])

    missing_dimensions: list[str] = []
    if not has_explicit_duration:
        missing_dimensions.append("duration")
    if not has_explicit_style:
        missing_dimensions.append("travel_style")
    if not has_explicit_pace:
        missing_dimensions.append("pace")
    if not has_explicit_group:
        missing_dimensions.append("group")
    if not has_explicit_budget:
        missing_dimensions.append("budget")

    if force_plan or answers:
        needs_clarification = False
    elif not has_explicit_dest:
        needs_clarification = True
    else:
        dims_present = sum([has_explicit_duration, has_explicit_style, has_explicit_pace, has_explicit_group, has_explicit_budget])
        # If fewer than 3 supporting dimensions specified, strategically ask clarifying questions
        needs_clarification = dims_present < 3

    # Handle Unknown Destination prompt (e.g. "plan a 3 day trip")
    if needs_clarification and trip_request.destination == "Unknown":
        dest_q = ClarificationQuestion(
            id="choose_destination",
            question="Which world-class destination would you like to explore?",
            category="destination",
            is_multi_select=False,
            options=[
                ClarificationOption(label="Goa, India — Beaches & Sunsets", value="Goa", icon="🌴"),
                ClarificationOption(label="Mumbai, India — Colonial Heritage & Coast", value="Mumbai", icon="🏛️"),
                ClarificationOption(label="Rajasthan, India — Royal Palaces & Forts", value="Rajasthan", icon="👑"),
                ClarificationOption(label="Kashmir, India — Serene Lakes & Valleys", value="Kashmir", icon="❄️"),
                ClarificationOption(label="Kyoto, Japan — Ancient Temples & Zen", value="Kyoto", icon="⛩️"),
                ClarificationOption(label="Lisbon, Portugal — Hills, Tram & Pastéis", value="Lisbon", icon="🏰"),
                ClarificationOption(label="Paris, France — Iconic Landmarks & Cafes", value="Paris", icon="🗼"),
            ]
        )
        generic_qs = _get_generic_clarification_questions("your trip")
        questions = [dest_q, generic_qs[0]]
        events.append(AgentEvent(
            event_type="clarification_needed",
            agent="intake_agent",
            message="I'd love to help plan your getaway! Where would you like to travel, and what travel vibe excites you?",
            data={
                "questions": [q.model_dump() for q in questions],
                "destination": "Unknown",
                "num_days": trip_request.num_days,
            }
        ))
        return {
            "trip_request": trip_request,
            "destination": "Unknown",
            "num_days": trip_request.num_days,
            "is_edit": False,
            "needs_clarification": True,
            "clarification_questions": questions,
            "events": events,
        }

    if needs_clarification and trip_request.destination != "Unknown":
        dest_lower = trip_request.destination.lower()
        matched_key = next((k for k in DESTINATION_QUESTIONS if k in dest_lower), None)

        if matched_key:
            # Use curated destination-specific template (fast, no LLM call)
            raw_qs = DESTINATION_QUESTIONS[matched_key]
            questions = [
                ClarificationQuestion(
                    id=q["id"],
                    question=q["question"],
                    category=q["category"],
                    is_multi_select=bool(q.get("is_multi_select", False)),
                    options=[ClarificationOption(**opt) for opt in q["options"]]
                )
                for q in raw_qs
            ]
        else:
            # Generate dynamic contextual questions from user's prompt targeting missing dimensions
            questions = await _generate_dynamic_clarification_questions(
                user_message=last_user_msg,
                destination=trip_request.destination,
                num_days=trip_request.num_days,
                missing_dimensions=missing_dimensions,
            )

        clarification_msg = (
            f"I've got {trip_request.num_days} days in {trip_request.destination} noted! "
            f"To customize this trip to your exact tastes, select a few quick preferences below (or generate immediately with standard defaults):"
            if has_explicit_duration else
            f"I've got {trip_request.destination} noted! To personalize your itinerary and daily rhythm, "
            f"choose your preferences below (or generate immediately with standard 3-day defaults):"
        )

        events.append(AgentEvent(
            event_type="clarification_needed",
            agent="intake_agent",
            message=clarification_msg,
            data={
                "questions": [q.model_dump() for q in questions],
                "destination": trip_request.destination,
                "num_days": trip_request.num_days,
            }
        ))

        return {
            "trip_request": trip_request,
            "destination": trip_request.destination,
            "num_days": trip_request.num_days,
            "is_edit": False,
            "needs_clarification": True,
            "clarification_questions": questions,
            "events": events,
        }

    # If complete or forced, proceed to planning
    events.append(AgentEvent(
        event_type="agent_step",
        agent="intake_agent",
        message=f"Trip preferences confirmed: {trip_request.num_days} days in {trip_request.destination} ({trip_request.travel_style.value} style, {trip_request.pace.value} pace).",
    ))

    return {
        "trip_request": trip_request,
        "destination": trip_request.destination,
        "num_days": trip_request.num_days,
        "is_edit": False,
        "needs_clarification": False,
        "clarification_questions": [],
        "events": events,
    }

