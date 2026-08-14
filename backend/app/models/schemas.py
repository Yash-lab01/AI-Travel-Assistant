from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date
from enum import Enum


class TravelStyle(str, Enum):
    popular = "popular"       # Mostly mainstream attractions
    balanced = "balanced"     # Mix of popular + niche
    niche = "niche"           # Mostly hidden gems


class TravelPace(str, Enum):
    relaxed = "relaxed"       # 2-3 stops/day
    moderate = "moderate"     # 4-5 stops/day
    intense = "intense"       # 6+ stops/day


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
    category: str  # e.g. "attraction", "restaurant", "viewpoint"
    description: str
    narration: Optional[str] = None  # Fine-tuned model output
    lat: float
    lon: float
    address: Optional[str] = None
    duration_minutes: int = Field(60, description="Estimated time to spend here")
    estimated_cost_usd: Optional[float] = None
    photo_urls: list[str] = Field(default_factory=list)
    rating: Optional[float] = None
    is_niche: bool = False
    niche_score: Optional[NicheScore] = None
    opening_hours: Optional[dict] = None
    travel_time_from_prev_minutes: Optional[int] = None  # Travel time from previous stop


class DayPlan(BaseModel):
    day_number: int
    date: Optional[date] = None
    theme: Optional[str] = None  # e.g. "Old Town & Hidden Cafés"
    stops: list[Stop] = Field(default_factory=list)
    daily_budget_usd: Optional[float] = None
    daily_cost_estimate_usd: Optional[float] = None
    weather_note: Optional[str] = None  # e.g. "Rain forecast — consider indoor alternatives"


class Itinerary(BaseModel):
    id: str
    trip_request: TripRequest
    days: list[DayPlan] = Field(default_factory=list)
    total_cost_estimate_usd: Optional[float] = None
    created_at: Optional[str] = None
    share_slug: Optional[str] = None


class AgentEvent(BaseModel):
    """Streamed over SSE to the frontend to show agent progress."""
    event_type: Literal[
        "agent_start",
        "tool_call",
        "tool_result",
        "agent_step",
        "narration_start",
        "narration_complete",
        "itinerary_ready",
        "error"
    ]
    agent: Optional[str] = None   # e.g. "intake_agent", "planner_agent"
    tool: Optional[str] = None    # e.g. "places_tool", "niche_scrape_tool"
    message: str = ""
    data: Optional[dict] = None   # Optional payload (e.g. partial stop data)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str
    existing_itinerary_id: Optional[str] = None  # For follow-up edits
