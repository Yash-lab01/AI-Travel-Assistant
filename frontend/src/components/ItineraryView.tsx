'use client';

import { Itinerary, DayPlan, Stop, StopEditRequest } from '@/types';
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

function StopCard({
  stop,
  index,
  destination,
  dayNumber,
  itineraryId,
  onStopAction,
}: {
  stop: Stop;
  index: number;
  destination?: string;
  dayNumber: number;
  itineraryId: string;
  onStopAction?: (req: StopEditRequest) => void;
}) {
  const [imgError, setImgError] = useState(false);
  if (!stop) return null;
  const icon = CATEGORY_ICONS[stop.category] ?? CATEGORY_ICONS.default;
  const photoUrl = stop.photo_urls && stop.photo_urls.length > 0 ? stop.photo_urls[0] : null;

  return (
    <>
      {index > 0 && stop.travel_time_from_prev_minutes !== undefined && (
        <div className="travel-connector">
          <span style={{ fontSize: 13 }}>➔</span>
          <span>{stop.travel_time_from_prev_minutes} min {stop.travel_time_from_prev_minutes <= 12 ? 'walk' : 'transit'}</span>
        </div>
      )}
      <div className={`stop-card ${stop.is_niche ? 'niche' : ''}`}>
        <div className="stop-card-image-wrap">
          {photoUrl && !imgError ? (
            <img
              src={photoUrl}
              alt={stop.name || 'Attraction'}
              className="stop-card-image"
              loading="lazy"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="stop-card-image-placeholder">
              {icon}
            </div>
          )}
        </div>

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

          {/* Quick Interactive Actions */}
          <div className="stop-card-actions">
            <button
              type="button"
              className="stop-action-btn swap"
              onClick={() => onStopAction?.({
                itinerary_id: itineraryId,
                day_number: dayNumber,
                stop_id: stop.id,
                stop_name: stop.name,
                action: 'swap',
              })}
              title="Swap this stop for an alternative place"
            >
              <span>🔄 Swap</span>
            </button>
            <button
              type="button"
              className="stop-action-btn remove"
              onClick={() => onStopAction?.({
                itinerary_id: itineraryId,
                day_number: dayNumber,
                stop_id: stop.id,
                stop_name: stop.name,
                action: 'remove',
              })}
              title="Remove this stop from Day plan"
            >
              <span>❌ Remove</span>
            </button>
            <button
              type="button"
              className="stop-action-btn info"
              onClick={() => onStopAction?.({
                itinerary_id: itineraryId,
                day_number: dayNumber,
                stop_id: stop.id,
                stop_name: stop.name,
                action: 'tell_me_more',
              })}
              title="Ask assistant for insider tips & storytelling"
            >
              <span>💬 Tell Me More</span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

function DayBanner({ day, destination }: { day: DayPlan; destination: string }) {
  const bgStyle = day.cover_image_url
    ? { backgroundImage: `url(${day.cover_image_url})` }
    : {};

  return (
    <div className="day-banner-card" style={bgStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8, marginBottom: 6 }}>
        <span style={{
          fontSize: 11,
          fontFamily: 'var(--font-label)',
          fontWeight: 700,
          color: 'var(--amber)',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          background: 'rgba(4, 14, 31, 0.75)',
          padding: '3px 10px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--glass-border-amber)',
        }}>
          Day {day.day_number}
        </span>
        {day.day_cost_estimate_usd !== undefined && (
          <span style={{
            fontSize: 12.5,
            color: 'var(--amber)',
            fontWeight: 700,
            background: 'rgba(4, 14, 31, 0.75)',
            padding: '3px 10px',
            borderRadius: 'var(--radius-full)',
            border: '1px solid rgba(255, 191, 0, 0.3)',
          }}>
            Est. {formatCost(day.day_cost_estimate_usd, destination, false)}
          </span>
        )}
      </div>

      <h3 className="day-theme-title">
        {day.theme || `Day ${day.day_number}`}
      </h3>

      {day.weather_note && (
        <div className="weather-badge">
          {day.weather_note}
        </div>
      )}
    </div>
  );
}

import ShareModal from './ShareModal';

interface Props {
  itinerary: Itinerary | null;
  isLoading: boolean;
  onStopAction?: (req: StopEditRequest) => void;
  onQuickEdit?: (instruction: string) => void;
}

export default function ItineraryView({ itinerary, isLoading, onStopAction, onQuickEdit }: Props) {
  const [activeDay, setActiveDay] = useState(0);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  const handleDownloadPdf = async () => {
    if (!itinerary || isDownloadingPdf) return;
    setIsDownloadingPdf(true);
    try {
      // First try direct POST with in-memory payload for instant guaranteed export
      const res = await fetch('http://localhost:8000/export/pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(itinerary),
      });

      if (!res.ok) {
        // Fallback to GET by ID
        const getRes = await fetch(`http://localhost:8000/export/pdf/${itinerary.id}`);
        if (!getRes.ok) throw new Error('PDF export failed');
        const blob = await getRes.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `WanderAI-${itinerary.trip_request?.destination || 'trip'}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        return;
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `WanderAI-${itinerary.trip_request?.destination || 'trip'}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF download error:', err);
      // Fallback: open in new tab
      window.open(`http://localhost:8000/export/pdf/${itinerary.id}`, '_blank');
    } finally {
      setIsDownloadingPdf(false);
    }
  };

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

  const destinationBgStyle = itinerary.cover_image_url
    ? { backgroundImage: `url(${itinerary.cover_image_url})` }
    : {};

  return (
    <div className="itinerary-workspace-container">
      {/* Destination Hero Banner */}
      {itinerary.cover_image_url && (
        <div className="itinerary-cover-banner" style={destinationBgStyle}>
          <div className="itinerary-cover-content">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <h2 className="itinerary-destination-title" style={{ textShadow: '0 2px 12px rgba(0,0,0,0.8)' }}>
                  {itinerary.trip_request?.num_days || days.length}-Day Journey to {destination}
                </h2>
                {nicheTotal > 0 && (
                  <span className="niche-badge" style={{ fontSize: 11, padding: '4px 12px' }}>
                    💎 {nicheTotal} Community Hidden Gems
                  </span>
                )}
              </div>
              <p style={{ fontSize: 13, color: '#d8e3fb', marginTop: 6, textShadow: '0 1px 4px rgba(0,0,0,0.8)' }}>
                Paced for <strong>{itinerary.trip_request?.pace || 'moderate'}</strong> speed · <strong>{itinerary.trip_request?.travel_style || 'balanced'}</strong> focus · Estimated Total: <strong style={{ color: 'var(--amber)' }}>{formatTotalCost(itinerary.total_cost_estimate_usd, destination)}</strong>
              </p>
            </div>

            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button
                onClick={handleDownloadPdf}
                disabled={isDownloadingPdf}
                className="btn-primary-sm"
                style={{ padding: '9px 16px', fontSize: 13, boxShadow: '0 4px 16px rgba(0,0,0,0.6)', cursor: isDownloadingPdf ? 'wait' : 'pointer' }}
                title="Download printable PDF travel guide"
              >
                <span>{isDownloadingPdf ? '⏳ PDF...' : '📄 PDF'}</span>
              </button>
              <button
                onClick={() => setIsShareModalOpen(true)}
                className="btn-primary-sm"
                style={{
                  padding: '9px 16px',
                  fontSize: 13,
                  background: 'rgba(0, 219, 231, 0.2)',
                  borderColor: '#00DBE7',
                  color: '#00DBE7',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.6)',
                }}
                title="Share itinerary link"
              >
                <span>🔗 Share</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Fallback Workspace Header if no cover image */}
      {!itinerary.cover_image_url && (
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

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              onClick={handleDownloadPdf}
              disabled={isDownloadingPdf}
              className="btn-primary-sm"
              style={{ padding: '8px 14px', fontSize: 13, cursor: isDownloadingPdf ? 'wait' : 'pointer' }}
              title="Download printable PDF travel guide"
            >
              <span>{isDownloadingPdf ? '⏳ PDF...' : '📄 PDF'}</span>
            </button>
            <button
              onClick={() => setIsShareModalOpen(true)}
              className="btn-primary-sm"
              style={{
                padding: '8px 14px',
                fontSize: 13,
                background: 'rgba(0, 219, 231, 0.15)',
                borderColor: '#00DBE7',
                color: '#00DBE7',
              }}
              title="Share itinerary link"
            >
              <span>🔗 Share</span>
            </button>
          </div>
        </div>
      )}

      {/* Share Modal Dialog */}
      <ShareModal
        isOpen={isShareModalOpen}
        onClose={() => setIsShareModalOpen(false)}
        itinerary={itinerary}
        onDownloadPdf={handleDownloadPdf}
        isDownloadingPdf={isDownloadingPdf}
      />

      {/* Quick Interactive Adjustments Strip */}
      <div className="quick-edits-bar">
        <span className="quick-edits-label">✨ Quick Adjustments:</span>
        <button
          type="button"
          className="quick-edit-chip"
          onClick={() => onQuickEdit?.("Make the trip pacing more relaxed with fewer stops")}
        >
          🧘 Relaxed Pacing
        </button>
        <button
          type="button"
          className="quick-edit-chip"
          onClick={() => onQuickEdit?.("Add more authentic local hidden gems and secret spots")}
        >
          💎 More Hidden Gems
        </button>
        <button
          type="button"
          className="quick-edit-chip"
          onClick={() => onQuickEdit?.("Focus recommendations on local food, cafes and street delicacies")}
        >
          🍲 Foodie & Cafes
        </button>
        <button
          type="button"
          className="quick-edit-chip"
          onClick={() => onQuickEdit?.("Add more nature, parks and scenic viewpoints")}
        >
          🌿 Scenic & Nature
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
            <DayBanner day={currentDay} destination={destination} />
          )}

          {validActiveDay === -1 && (
            <div className="day-banner-card" style={destinationBgStyle}>
              <h3 className="day-theme-title">Complete Journey Overview</h3>
              <p style={{ fontSize: 13, color: '#d8e3fb', marginTop: 4, textShadow: '0 1px 4px rgba(0,0,0,0.8)' }}>
                Viewing all {allStops.length} locations across {days.length} days on the interactive map.
              </p>
            </div>
          )}

          {/* Sequential Stops */}
          <div className="stops-timeline-list">
            {displayedStops.map((stop, idx) => {
              // Derive day number for this stop
              const stopDayNumber = validActiveDay === -1
                ? (days.find(d => d.stops?.some(s => s.id === stop.id))?.day_number || 1)
                : (currentDay?.day_number || 1);

              return (
                <StopCard
                  key={stop.id || idx}
                  stop={stop}
                  index={idx}
                  destination={destination}
                  dayNumber={stopDayNumber}
                  itineraryId={itinerary.id}
                  onStopAction={onStopAction}
                />
              );
            })}
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
