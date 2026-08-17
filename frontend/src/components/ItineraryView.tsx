'use client';

import { Itinerary, DayPlan, Stop } from '@/types';
import { useState, lazy, Suspense } from 'react';

const MapView = lazy(() => import('./MapView'));

const CATEGORY_ICONS: Record<string, string> = {
  attraction: '🏛️',
  restaurant: '🍽️',
  viewpoint:  '🌅',
  museum:     '🖼️',
  park:       '🌿',
  market:     '🛍️',
  cafe:       '☕',
  bar:        '🍷',
  beach:      '🏖️',
  default:    '📍',
};

function StopCard({ stop, index }: { stop: Stop; index: number }) {
  const icon = CATEGORY_ICONS[stop.category] ?? CATEGORY_ICONS.default;

  return (
    <>
      {index > 0 && stop.travel_time_from_prev_minutes && (
        <div className="travel-connector">
          🚶 {stop.travel_time_from_prev_minutes} min walk / transit
        </div>
      )}
      <div className={`stop-card ${stop.is_niche ? 'niche' : ''}`}>
        {stop.photo_urls.length > 0 ? (
          <img
            src={stop.photo_urls[0]}
            alt={stop.name}
            className="stop-card-image"
            style={{ display: 'block' }}
          />
        ) : (
          <div className="stop-card-image">{icon}</div>
        )}
        <div className="stop-card-body">
          <div className="stop-card-top">
            <div className="stop-name">{stop.name}</div>
            {stop.is_niche && (
              <div className="niche-badge" title="Surfaced via high community sentiment & low tourist saturation">
                💎 HIDDEN GEM {stop.niche_score ? `${(stop.niche_score.hidden_gem_score * 100).toFixed(0)}%` : ''}
              </div>
            )}
          </div>

          {stop.narration && (
            <p className="stop-narration">"{stop.narration}"</p>
          )}
          {!stop.narration && (
            <p className="stop-narration" style={{ fontStyle: 'normal' }}>
              {stop.description}
            </p>
          )}

          <div className="stop-meta">
            <span className="stop-meta-chip">⏱️ {stop.duration_minutes} min</span>
            {stop.estimated_cost_usd !== undefined && (
              <span className="stop-meta-chip">💵 ${stop.estimated_cost_usd}</span>
            )}
            {stop.rating && (
              <span className="stop-meta-chip">★ {stop.rating.toFixed(1)}</span>
            )}
            <span className="stop-meta-chip" style={{ textTransform: 'capitalize' }}>
              {icon} {stop.category}
            </span>
            {stop.source && (
              <span className="stop-meta-chip" style={{ color: 'var(--teal)' }}>
                via {stop.source}
              </span>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

function DayView({ day, budget }: { day: DayPlan; budget?: number }) {
  const spent = day.daily_cost_estimate_usd ?? 0;
  const pct = budget ? Math.min((spent / budget) * 100, 100) : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className="day-header">
        <div className="day-number-badge">{day.day_number}</div>
        <div>
          {day.theme && <div className="day-theme">{day.theme}</div>}
          {day.date && (
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {new Date(day.date).toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
            </div>
          )}
        </div>
      </div>

      {day.weather_note && (
        <div style={{
          background: 'rgba(248,113,113,0.08)',
          border: '1px solid rgba(248,113,113,0.25)',
          borderRadius: 'var(--radius-md)',
          padding: '10px 14px',
          fontSize: 13,
          color: 'var(--coral)',
          display: 'flex',
          gap: 8,
          alignItems: 'center',
        }}>
          🌦️ {day.weather_note}
        </div>
      )}

      {budget && spent > 0 && (
        <div className="budget-bar-container">
          <div className="budget-bar-label">
            <span>Daily spend estimate</span>
            <span><strong style={{ color: 'var(--text-primary)' }}>${spent.toFixed(0)}</strong> / ${budget.toFixed(0)} budget</span>
          </div>
          <div className="budget-bar-track">
            <div className="budget-bar-fill" style={{ width: `${pct}%` }} />
          </div>
        </div>
      )}

      {day.stops.map((stop, i) => (
        <StopCard key={stop.id} stop={stop} index={i} />
      ))}
    </div>
  );
}

interface Props {
  itinerary: Itinerary | null;
  isLoading: boolean;
}

export default function ItineraryView({ itinerary, isLoading }: Props) {
  const [activeDay, setActiveDay] = useState(0);

  if (isLoading) {
    return (
      <div className="itinerary-panel">
        <div className="empty-state">
          <div className="empty-state-icon">🧭</div>
          <div className="empty-state-title">Multi-Agent Swarm Orchestrating...</div>
          <div className="empty-state-desc">
            Extracting requirements, querying live place databases, spatial clustering, and evaluating hidden gem scores.
          </div>
        </div>
      </div>
    );
  }

  if (!itinerary) {
    return (
      <div className="itinerary-panel">
        <div className="empty-state">
          <div className="empty-state-icon">✈️</div>
          <div className="empty-state-title">Your Itinerary Will Materialize Here</div>
          <div className="empty-state-desc">
            Type a destination in the chat or click one of the curated prompt chips to generate a tailored itinerary complete with hidden gems and map routing.
          </div>
        </div>
      </div>
    );
  }

  const perDayBudget = itinerary.trip_request.budget_usd
    ? itinerary.trip_request.budget_usd / itinerary.days.length
    : undefined;

  const totalNicheCount = itinerary.days.flatMap(d => d.stops).filter(s => s.is_niche).length;

  return (
    <div className="itinerary-panel">
      {/* Day tabs */}
      <div className="day-tabs">
        {itinerary.days.map((day, i) => (
          <button
            key={i}
            className={`day-tab ${activeDay === i ? 'active' : ''}`}
            onClick={() => setActiveDay(i)}
          >
            Day {day.day_number}{day.theme ? ` · ${day.theme.split(' ').slice(0, 2).join(' ')}` : ''}
          </button>
        ))}
      </div>

      {/* Trip summary strip */}
      <div style={{
        display: 'flex',
        gap: 18,
        padding: '10px 24px',
        borderBottom: '1px solid var(--glass-border)',
        background: 'rgba(6, 17, 33, 0.85)',
        backdropFilter: 'blur(16px)',
        fontSize: 12,
        color: 'var(--text-secondary)',
        alignItems: 'center',
        flexWrap: 'wrap',
        fontFamily: 'var(--font-label)',
      }}>
        <span>📍 <strong style={{ color: 'var(--amber)', fontFamily: 'var(--font-headline)', fontStyle: 'italic', fontSize: 14 }}>{itinerary.trip_request.destination}</strong></span>
        <span>📅 {itinerary.days.length} Days</span>
        {itinerary.trip_request.budget_usd && (
          <span>💵 ${itinerary.trip_request.budget_usd.toLocaleString()} Budget</span>
        )}
        {itinerary.total_cost_estimate_usd && (
          <span style={{ color: 'var(--text-muted)' }}>~${itinerary.total_cost_estimate_usd.toLocaleString()} Est. Total</span>
        )}
        <span style={{ marginLeft: 'auto', color: 'var(--teal)', fontWeight: 600 }}>
          💎 {totalNicheCount} Hidden {totalNicheCount === 1 ? 'Gem' : 'Gems'} Discovered
        </span>
      </div>

      {/* Mapbox Map View */}
      <div style={{ height: '240px', flexShrink: 0, borderBottom: '1px solid var(--glass-border)' }}>
        <Suspense fallback={
          <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
            Loading nocturnal map...
          </div>
        }>
          <MapView
            stops={itinerary.days[activeDay]?.stops ?? []}
            activeDay={activeDay}
          />
        </Suspense>
      </div>

      {/* Active Day Content */}
      <div className="itinerary-content">
        {itinerary.days[activeDay] && (
          <DayView day={itinerary.days[activeDay]} budget={perDayBudget} />
        )}
      </div>
    </div>
  );
}
