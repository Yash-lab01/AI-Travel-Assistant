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
    time_slot: Optional[str] = None # e.g. "09:30 AM - 11:00 AM"


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


class EditIntent(str, Enum):
    new_trip       = "new_trip"        # Start a brand new destination / trip
    swap_stop      = "swap_stop"       # Replace a specific stop with an alternative
    remove_stop    = "remove_stop"     # Delete a stop from a day
    adjust_pace    = "adjust_pace"     # Change pacing (e.g. relaxed, fast)
    change_budget  = "change_budget"   # Adjust budget or travel style
    tell_me_more   = "tell_me_more"    # Ask for insider tips, story or details about a place
    general_edit   = "general_edit"    # Conversational modification to the itinerary


class StopEditRequest(BaseModel):
    itinerary_id: str
    day_number: int
    stop_id: Optional[str] = None
    stop_name: Optional[str] = None
    action: Literal["swap", "remove", "tell_me_more"] = "swap"
    custom_preference: Optional[str] = None  # e.g. "beach cafe", "museum", "scenic sunset point"


class StopReorderRequest(BaseModel):
    day_number: int
    stop_ids: list[str] = Field(..., description="Ordered list of stop IDs for this day")


class StopFeedbackRequest(BaseModel):
    itinerary_id: Optional[str] = None
    stop_id: str
    stop_name: str
    destination: str
    rating: Literal[1, -1]  # 1 for thumbs-up, -1 for thumbs-down
    category: Optional[str] = None
    is_niche: bool = False
    comment: Optional[str] = None


class PackingListItem(BaseModel):
    item: str
    category: str       # "clothing", "weather", "electronics", "health_docs", "activity"
    reason: Optional[str] = None
    is_essential: bool = True


class PackingListCategory(BaseModel):
    name: str
    icon: str
    items: list[PackingListItem] = Field(default_factory=list)


class PackingListResponse(BaseModel):
    destination: str
    weather_summary: Optional[str] = None
    categories: list[PackingListCategory] = Field(default_factory=list)


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
        "assistant_message",
        "error"
    ]
    agent: Optional[str] = None   # e.g. "intake_agent", "planner_agent", "editor_agent"
    tool: Optional[str] = None    # e.g. "places_tool", "niche_scrape_tool", "routing_tool"
    message: str = ""
    data: Optional[dict] = None   # Optional payload (e.g. clarification questions, partial stop data, assistant answer)


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
    action: Optional[str] = None                 # Explicit action: "swap" | "remove" | "tell_me_more"
    target_day: Optional[int] = None             # Target day number for edits
    target_stop_id: Optional[str] = None         # Specific stop id being targeted
    target_stop_name: Optional[str] = None       # Specific stop name being targeted


