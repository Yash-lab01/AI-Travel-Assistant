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
}

export interface DayPlan {
  day_number: number;
  date?: string;
  theme?: string;
  stops: Stop[];
  daily_budget_usd?: number;
  daily_cost_estimate_usd?: number;
  weather_note?: string;
}

export interface Itinerary {
  id: string;
  trip_request: TripRequest;
  days: DayPlan[];
  total_cost_estimate_usd?: number;
  created_at?: string;
  share_slug?: string;
}

export interface AgentEvent {
  event_type:
    | 'agent_start'
    | 'tool_call'
    | 'tool_result'
    | 'agent_step'
    | 'narration_start'
    | 'narration_complete'
    | 'itinerary_ready'
    | 'error';
  agent?: string;
  tool?: string;
  message: string;
  data?: Record<string, unknown>;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}
