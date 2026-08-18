'use client';

import { Itinerary, DayPlan, Stop } from '@/types';
import { useState, lazy, Suspense } from 'react';
import { formatCost, formatTotalCost } from '@/utils/currency';

const MapView = lazy(() => import('./MapView'));

const CATEGORY_ICONS: Record<string, string> = {
  attraction: '🏛️',
  restaurant: '🍲',
  viewpoint:  '🌄',
  museum:     '🖼️',
  park:       '🌿',
  market:     '🛍️',
  cafe:       '☕',
  bar:        '🍸',
  beach:      '🏖️',
  default:    '📍',
};

function StopCard({ stop, index, destination }: { stop: Stop; index: number; destination?: string }) {
  if (!stop) return null;
  const icon = CATEGORY_ICONS[stop.category] ?? CATEGORY_ICONS.default;

  return (
    <>
      {index > 0 && stop.travel_time_from_prev_minutes !== undefined && (
        <div className="travel-connector">
          <span style={{ fontSize: 13 }}>➔</span>
          <span>{stop.travel_time_from_prev_minutes} min {stop.travel_time_from_prev_minutes <= 12 ? 'walk' : 'transit'}</span>
        </div>
      )}
      <div className={`stop-card ${stop.is_niche ? 'niche' : ''}`}>
        {stop.photo_urls && stop.photo_urls.length > 0 ? (
          <img
            src={stop.photo_urls[0]}
            alt={stop.name || 'Attraction'}
            className="stop-card-image"
            style={{ display: 'block' }}
          />
        ) : (
          <div className="stop-card-image">{icon}</div>
        )}
        <div className="stop-card-body">
          <div className="stop-card-top">
            <div className="stop-name">{stop.name || 'Attraction'}</div>
            {stop.is_niche && (
              <div className="niche-badge" title="Surfaced via high community sentiment & low tourist saturation">
                💎 HIDDEN GEM {stop.niche_score ? `${(stop.niche_score.hidden_gem_score * 100).toFixed(0)}%` : ''}
              </div>
            )}
          </div>

          {stop.narration ? (
            <p className="stop-narration">"{stop.narration}"</p>
          ) : (
            <p className="stop-narration" style={{ fontStyle: 'normal' }}>
              {stop.description || 'Curated stop in your journey.'}
            </p>
          )}

          <div className="stop-meta">
            <span className="stop-category-pill">{stop.category || 'attraction'}</span>
            <span style={{ color: 'var(--text-muted)' }}>⏱️ {stop.duration_minutes || 60} min</span>
            {stop.estimated_cost_usd !== undefined && (
              <span className="stop-cost">{formatCost(stop.estimated_cost_usd, destination)}</span>
            )}
            {stop.rating && (
              <span style={{ color: 'var(--amber)' }}>★ {stop.rating}</span>
            )}
          </div>
        </div>
      </div>
    </>
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
      <div className="itinerary-empty-card" style={{ minHeight: 380 }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
          <div style={{ width: 44, height: 44, borderRadius: '50%', border: '3px solid var(--glass-border-amber)', borderTopColor: 'var(--amber)', animation: 'spin 1s linear infinite' }} />
          <div style={{ fontFamily: 'var(--font-heading)', fontSize: 18, color: '#fff' }}>
            Designing Your Custom Route...
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center', maxWidth: 360 }}>
            Orchestrating place discovery, community hidden gem scoring, Open-Meteo weather forecasts, and walking routes.
          </div>
        </div>
      </div>
    );
  }

  if (!itinerary) {
    return null;
  }

  const destination = itinerary.trip_request?.destination || 'Destination';
  const days = itinerary.days || [];
  
  // Safe day indexing
  const validActiveDay = (activeDay >= 0 && activeDay < days.length) ? activeDay : (activeDay === -1 ? -1 : 0);
  const currentDay: DayPlan | undefined = validActiveDay === -1 ? undefined : days[validActiveDay];
  const allStops = days.flatMap(d => d.stops || []);
  const displayedStops = validActiveDay === -1 ? allStops : (currentDay?.stops || []);
  const nicheTotal = allStops.filter(s => s.is_niche).length;

  return (
    <div className="itinerary-workspace-container">
      {/* Workspace Top Header Bar */}
      <div className="itinerary-workspace-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <h2 className="itinerary-destination-title">
              {itinerary.trip_request?.num_days || days.length}-Day Journey to {destination}
            </h2>
            {nicheTotal > 0 && (
              <span className="niche-badge" style={{ fontSize: 11, padding: '4px 10px' }}>
                💎 {nicheTotal} Community Hidden Gems
              </span>
            )}
          </div>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
            Paced for {itinerary.trip_request?.pace || 'moderate'} speed · {itinerary.trip_request?.travel_style || 'balanced'} focus · Estimated Total: <strong style={{ color: 'var(--amber)' }}>{formatTotalCost(itinerary.total_cost_estimate_usd, destination)}</strong>
          </p>
        </div>

        <button
          onClick={() => window.open(`http://localhost:8000/export/pdf/${itinerary.id}`, '_blank')}
          className="btn-primary-sm"
          style={{ padding: '8px 16px', fontSize: 13 }}
        >
          <span>📄 Export Itinerary</span>
        </button>
      </div>

      {/* Day Selector Navigation Strip */}
      <div className="day-tabs-strip">
        {days.map((day, i) => (
          <button
            key={day.day_number || i}
            className={`day-tab-btn ${validActiveDay === i ? 'active' : ''}`}
            onClick={() => setActiveDay(i)}
          >
            <span className="day-tab-num">Day {day.day_number || i + 1}</span>
            <span className="day-tab-theme">{day.theme || `Day ${day.day_number || i + 1}`}</span>
          </button>
        ))}
        <button
          className={`day-tab-btn ${validActiveDay === -1 ? 'active' : ''}`}
          onClick={() => setActiveDay(-1)}
        >
          <span className="day-tab-num">🗺️ Overview</span>
          <span className="day-tab-theme">All {allStops.length} Stops</span>
        </button>
      </div>

      {/* Side-by-Side Dual-Pane Grid: Timeline (Left) + Interactive Map (Right) */}
      <div className="itinerary-dual-grid">
        {/* Left Column: Day Timeline */}
        <div className="itinerary-timeline-pane">
          {validActiveDay !== -1 && currentDay && (
            <div className="day-header-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                <h3 className="day-theme-title">
                  Day {currentDay.day_number}: {currentDay.theme}
                </h3>
                {currentDay.day_cost_estimate_usd !== undefined && (
                  <span style={{ fontSize: 13, color: 'var(--amber)', fontWeight: 600 }}>
                    Est. {formatCost(currentDay.day_cost_estimate_usd, destination, false)}
                  </span>
                )}
              </div>

              {/* Weather Note Badge */}
              {currentDay.weather_note && (
                <div className="weather-badge">
                  {currentDay.weather_note}
                </div>
              )}
            </div>
          )}

          {validActiveDay === -1 && (
            <div className="day-header-card">
              <h3 className="day-theme-title">Complete Journey Overview</h3>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                Viewing all {allStops.length} locations across {days.length} days on the interactive map.
              </p>
            </div>
          )}

          {/* Sequential Stops */}
          <div className="stops-timeline-list">
            {displayedStops.map((stop, idx) => (
              <StopCard key={stop.id || idx} stop={stop} index={idx} destination={destination} />
            ))}
          </div>
        </div>

        {/* Right Column: Sticky Interactive Leaflet Map */}
        <div className="itinerary-map-pane">
          <div className="sticky-map-wrapper">
            <Suspense fallback={
              <div className="map-loading-placeholder">
                <div style={{ color: 'var(--teal)', fontSize: 13 }}>Loading Nocturnal Map...</div>
              </div>
            }>
              <MapView stops={displayedStops} activeDay={validActiveDay} />
            </Suspense>
          </div>
        </div>
      </div>
    </div>
  );
}
