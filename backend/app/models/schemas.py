from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date
from enum import Enum


class TravelStyle(str, Enum):
    balanced  = "balanced"    # mix of popular + niche
    popular   = "popular"     # mostly iconic landmarks
    niche     = "niche"       # hidden gems & off-the-beaten-path
    cultural  = "cultural"
    adventure = "adventure"
    foodie    = "foodie"
    relaxed   = "relaxed"


class TravelPace(str, Enum):
    slow     = "slow"         # 2-3 stops/day
    relaxed  = "relaxed"      # alias for slow
    moderate = "moderate"     # 4-5 stops/day
    fast     = "fast"         # 6+ stops/day
    intense  = "intense"      # alias for fast


class GroupType(str, Enum):
    solo = "solo"
    couple = "couple"
    family = "family"
    friends = "friends"


class TripRequest(BaseModel):
    destination: str = Field(..., description="City or region to travel to")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    num_days: Optional[int] = Field(None, ge=1, le=30)
    budget_usd: Optional[float] = Field(None, ge=0, description="Total trip budget in USD")
    travel_style: TravelStyle = TravelStyle.balanced
    niche_weight: float = Field(
        0.5, ge=0.0, le=1.0,
        description="0=fully popular, 1=fully hidden gems"
    )
    pace: TravelPace = TravelPace.moderate
    group_type: GroupType = GroupType.solo
    interests: list[str] = Field(default_factory=list, description="e.g. ['food', 'history', 'art']")
    region_preference: Optional[str] = None   # e.g. "North Goa (beaches/nightlife)" or "South Goa (heritage/peace)"
    raw_message: Optional[str] = None  # Original user message for context


class NicheScore(BaseModel):
    spot_name: str
    destination: str
    mention_count: int = 0
    avg_sentiment: float = Field(0.0, ge=-1.0, le=1.0)
    source_diversity: int = Field(0, description="Number of distinct source types mentioning this spot")
    google_review_count: Optional[int] = None
    hidden_gem_score: float = Field(0.0, ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list)


class Stop(BaseModel):
    id: str
    name: str
    category: str               # "attraction", "restaurant", "cafe", "viewpoint", "park", "museum", "beach", "market"
    description: str
    narration: str              # Written by fine-tuned model (or cloud LLM fallback)
    lat: float
    lon: float
    address: Optional[str] = None
    duration_minutes: int = 60
    estimated_cost_usd: Optional[float] = None
    photo_urls: list[str] = Field(default_factory=list)
    rating: Optional[float] = None
    review_count: Optional[int] = None
    source: Optional[str] = None # e.g. "reddit", "opentripmap", "tavily_blog"
    is_niche: bool = False
    niche_score: Optional[NicheScore] = None
    opening_hours: Optional[dict] = None
    travel_time_from_prev_minutes: Optional[int] = None


class DayPlan(BaseModel):
    day_number: int
    theme: str                  # e.g. "Historic Alfama & Fado Nights" or "North Goa Coastal Forts"
    date: Optional[str] = None
    stops: list[Stop] = Field(default_factory=list)
    day_cost_estimate_usd: Optional[float] = None
    weather_note: Optional[str] = None
    cover_image_url: Optional[str] = None


class Itinerary(BaseModel):
    id: str
    trip_request: TripRequest
    days: list[DayPlan] = Field(default_factory=list)
    total_cost_estimate_usd: Optional[float] = None
    created_at: Optional[str] = None
    share_slug: Optional[str] = None
    cover_image_url: Optional[str] = None


class ClarificationOption(BaseModel):
    label: str
    value: str
    icon: Optional[str] = None


class ClarificationQuestion(BaseModel):
    id: str
    question: str
    category: str   # "region_vibe" | "pace" | "budget" | "travel_style" | "group"
    options: list[ClarificationOption] = Field(default_factory=list)


class AgentEvent(BaseModel):
    """Streamed over SSE to the frontend to show agent progress."""
    event_type: Literal[
        "agent_start",
        "tool_call",
        "tool_result",
        "agent_step",
        "clarification_needed",
        "day_ready",
        "narration_start",
        "narration_complete",
        "itinerary_ready",
        "error"
    ]
    agent: Optional[str] = None   # e.g. "intake_agent", "planner_agent"
    tool: Optional[str] = None    # e.g. "places_tool", "niche_scrape_tool"
    message: str = ""
    data: Optional[dict] = None   # Optional payload (e.g. clarification questions, partial stop data)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str
    destination: Optional[str] = None            # Explicit destination if preserved across turns
    num_days: Optional[int] = None               # Explicit days if preserved across turns
    existing_itinerary_id: Optional[str] = None  # For follow-up edits
    force_plan: bool = False                     # If True, bypasses clarification questions
    answers: Optional[dict[str, str]] = None     # User-selected clarification answers

