// Types matching backend Pydantic schemas

export interface TripRequest {
  destination: string;
  start_date?: string;
  end_date?: string;
  num_days?: number;
  budget_usd?: number;
  travel_style: 'popular' | 'balanced' | 'niche' | 'cultural' | 'adventure' | 'foodie' | 'relaxed';
  niche_weight: number;
  pace: 'slow' | 'relaxed' | 'moderate' | 'fast' | 'intense';
  group_type: 'solo' | 'couple' | 'family' | 'friends';
  interests: string[];
  region_preference?: string;
  raw_message?: string;
}

export interface NicheScore {
  spot_name: string;
  destination: string;
  mention_count: number;
  avg_sentiment: number;
  source_diversity: number;
  google_review_count?: number;
  hidden_gem_score: number;
  sources: string[];
}

export interface Stop {
  id: string;
  name: string;
  category: string;
  description: string;
  narration?: string;
  lat: number;
  lon: number;
  address?: string;
  duration_minutes: number;
  estimated_cost_usd?: number;
  photo_urls: string[];
  rating?: number;
  review_count?: number;
  source?: string;
  is_niche: boolean;
  niche_score?: NicheScore;
  opening_hours?: Record<string, string>;
  travel_time_from_prev_minutes?: number;
  time_slot?: string;
}

export interface DayPlan {
  day_number: number;
  date?: string;
  theme?: string;
  stops: Stop[];
  day_cost_estimate_usd?: number;
  weather_note?: string;
  cover_image_url?: string;
}

export interface Itinerary {
  id: string;
  trip_request: TripRequest;
  days: DayPlan[];
  total_cost_estimate_usd?: number;
  created_at?: string;
  share_slug?: string;
  cover_image_url?: string;
}

export interface ClarificationOption {
  label: string;
  value: string;
  icon?: string;
}

export interface ClarificationQuestion {
  id: string;
  question: string;
  category: string;
  options: ClarificationOption[];
}

export type StopEditAction = 'swap' | 'remove' | 'tell_me_more';

export interface StopEditRequest {
  itinerary_id: string;
  day_number: number;
  stop_id?: string;
  stop_name?: string;
  action: StopEditAction;
  custom_preference?: string;
}

export interface StopFeedback {
  stop_id: string;
  stop_name: string;
  destination: string;
  rating: 1 | -1;
  itinerary_id?: string;
  category?: string;
  is_niche?: boolean;
}

export interface PackingListItem {
  item: string;
  category: string;
  reason?: string;
  is_essential: boolean;
}

export interface PackingListCategory {
  name: string;
  icon: string;
  items: PackingListItem[];
}

export interface PackingListResponse {
  destination: string;
  weather_summary?: string;
  categories: PackingListCategory[];
}

export interface AgentEvent {
  event_type:
    | 'agent_start'
    | 'tool_call'
    | 'tool_result'
    | 'agent_step'
    | 'clarification_needed'
    | 'day_ready'
    | 'narration_start'
    | 'narration_complete'
    | 'itinerary_ready'
    | 'assistant_message'
    | 'error';
  agent?: string;
  tool?: string;
  message: string;
  data?: {
    questions?: ClarificationQuestion[];
    destination?: string;
    num_days?: number;
    day_number?: number;
    day_plan?: DayPlan;
    stop_name?: string;
    [key: string]: unknown;
  };
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  questions?: ClarificationQuestion[];
  isClarification?: boolean;
  destination?: string;
  num_days?: number;
}

export interface TripHistorySummary {
  id: string;
  destination: string;
  num_days: number;
  total_cost_usd?: number;
  cover_image_url?: string | null;
  created_at: string;
}

export interface TripHistoryRecord extends TripHistorySummary {
  itinerary?: Itinerary;
}

