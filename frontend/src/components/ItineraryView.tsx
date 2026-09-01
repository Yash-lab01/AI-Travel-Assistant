'use client';

import { Itinerary, DayPlan, Stop, StopEditRequest } from '@/types';
import { useState, lazy, Suspense, useEffect } from 'react';
import { formatCost, formatTotalCost } from '@/utils/currency';
import { calculateDayTimeline, recalculateSequentialTransit } from '@/utils/timeline';
import ShareModal from './ShareModal';
import PackingListModal from './PackingListModal';
import { useToast } from './Toast';

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

function AnimatedCost({ value, destination }: { value?: number; destination?: string }) {
  const [displayVal, setDisplayVal] = useState(0);
  useEffect(() => {
    if (value === undefined || value === null) return;
    let current = 0;
    const target = Math.round(value);
    const step = Math.max(1, Math.floor(target / 20));
    const timer = setInterval(() => {
      current += step;
      if (current >= target) {
        setDisplayVal(target);
        clearInterval(timer);
      } else {
        setDisplayVal(current);
      }
    }, 20);
    return () => clearInterval(timer);
  }, [value]);

  if (value === undefined || value === null) return null;
  return <span>{formatTotalCost(displayVal, destination)}</span>;
}

function StopCard({
  stop,
  index,
  destination,
  dayNumber,
  itineraryId,
  timeSlot,
  transitBefore,
  onStopAction,
  onFeedback,
  feedbackState,
  isDraggable,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd,
  isDragOver,
}: {
  stop: Stop;
  index: number;
  destination?: string;
  dayNumber: number;
  itineraryId: string;
  timeSlot?: string;
  transitBefore?: number;
  onStopAction?: (req: StopEditRequest) => void;
  onFeedback?: (stopId: string, stopName: string, rating: 1 | -1, category?: string, isNiche?: boolean) => void;
  feedbackState?: 1 | -1 | null;
  isDraggable?: boolean;
  onDragStart?: (e: React.DragEvent, index: number) => void;
  onDragOver?: (e: React.DragEvent, index: number) => void;
  onDrop?: (e: React.DragEvent, index: number) => void;
  onDragEnd?: (e: React.DragEvent) => void;
  isDragOver?: boolean;
}) {
  const [imgError, setImgError] = useState(false);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });

  if (!stop) return null;
  const icon = CATEGORY_ICONS[stop.category] ?? CATEGORY_ICONS.default;
  const photoUrl = stop.photo_urls && stop.photo_urls.length > 0 ? stop.photo_urls[0] : null;
  const transitMin = transitBefore !== undefined ? transitBefore : stop.travel_time_from_prev_minutes;

  const mapsUrl = stop.lat && stop.lon
    ? `https://www.google.com/maps/dir/?api=1&destination=${stop.lat},${stop.lon}&travelmode=walking`
    : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${stop.name}, ${destination || ''}`)}`;

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientY - rect.top - rect.height / 2) / 16;
    const y = -(e.clientX - rect.left - rect.width / 2) / 16;
    setTilt({ x: Math.max(-5, Math.min(5, x)), y: Math.max(-5, Math.min(5, y)) });
  };

  const handleMouseLeave = () => {
    setTilt({ x: 0, y: 0 });
  };

  return (
    <div
      draggable={isDraggable}
      onDragStart={(e) => onDragStart?.(e, index)}
      onDragOver={(e) => onDragOver?.(e, index)}
      onDrop={(e) => onDrop?.(e, index)}
      onDragEnd={onDragEnd}
      className="stop-card-stagger"
      style={{
        transition: 'transform 200ms ease, opacity 200ms ease',
        borderTop: isDragOver ? '2px solid var(--teal, #00DBE7)' : 'none',
      }}
    >
      {index > 0 && transitMin !== undefined && transitMin > 0 && (
        <div className="travel-connector">
          <span style={{ fontSize: 13, color: 'var(--teal)' }}>➔</span>
          <span>{transitMin} min {transitMin <= 12 ? 'walk' : 'transit'}</span>
        </div>
      )}

      <div
        className={`stop-card ${stop.is_niche ? 'niche' : ''}`}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{
          transform: `perspective(900px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
        }}
      >
        {/* Full-Bleed Top Photographic Banner */}
        <div className="stop-card-banner">
          {photoUrl && !imgError ? (
            <img
              src={photoUrl}
              alt={stop.name || 'Attraction'}
              className="stop-card-banner-img"
              loading="lazy"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="stop-card-image-placeholder">
              {icon}
            </div>
          )}
          
          <div className="stop-card-banner-scrim" />

          {/* Floating Top Chips: Grip handle + Category + Time Slot */}
          <div className="stop-card-banner-top-chips">
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {isDraggable && (
                <div
                  className="stop-drag-handle"
                  title="Drag to reorder stops"
                  style={{
                    background: 'rgba(4, 14, 31, 0.75)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '3px 8px',
                    color: 'var(--text-secondary)',
                    cursor: 'grab',
                    fontSize: 13,
                    userSelect: 'none',
                    lineHeight: 1,
                  }}
                >
                  ⋮⋮
                </div>
              )}
              <span className="stop-category-pill" style={{ background: 'rgba(4, 14, 31, 0.75)', backdropFilter: 'blur(10px)' }}>
                {icon} {stop.category || 'attraction'}
              </span>
            </div>

            {timeSlot && (
              <span
                style={{
                  fontSize: 11,
                  fontFamily: 'var(--font-mono, monospace)',
                  fontWeight: 700,
                  color: 'var(--teal, #00DBE7)',
                  background: 'rgba(4, 14, 31, 0.85)',
                  border: '1px solid rgba(0, 219, 231, 0.4)',
                  padding: '3px 9px',
                  borderRadius: 'var(--radius-full)',
                  boxShadow: '0 2px 10px rgba(0, 0, 0, 0.5)',
                }}
              >
                🕒 {timeSlot}
              </span>
            )}
          </div>

          {/* Floating Bottom Chips: Hidden Gem + Star Rating */}
          <div className="stop-card-banner-bottom-chips">
            {stop.is_niche ? (
              <div className="niche-badge" title="Surfaced via high community sentiment & low tourist saturation">
                💎 LOCAL FAVORITE {stop.niche_score ? `${(stop.niche_score.hidden_gem_score * 100).toFixed(0)}%` : ''}
              </div>
            ) : <div />}

            {stop.rating && (
              <span
                style={{
                  color: 'var(--amber, #FFBF00)',
                  background: 'rgba(4, 14, 31, 0.85)',
                  border: '1px solid rgba(255, 191, 0, 0.3)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: 11,
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 700,
                }}
              >
                ★ {stop.rating}
              </span>
            )}
          </div>
        </div>

        {/* Card Body Information */}
        <div className="stop-card-body">
          <div className="stop-card-top">
            <h4 className="stop-name">{stop.name || 'Attraction'}</h4>
            {stop.estimated_cost_usd !== undefined && (
              <span className="stop-cost">{formatCost(stop.estimated_cost_usd, destination)}</span>
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
            <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              ⏱️ {stop.duration_minutes || 60} min
            </span>
            {stop.address && (
              <span style={{ color: 'var(--text-muted)', fontSize: 11, maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={stop.address}>
                📍 {stop.address}
              </span>
            )}
          </div>

          {/* Actions & Feedback Row */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginTop: 4, paddingTop: 10, borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
            <div className="stop-card-actions" style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
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
                <span>💬 Tips</span>
              </button>
              <a
                href={mapsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="stop-action-btn"
                style={{
                  textDecoration: 'none',
                  background: 'rgba(0, 219, 231, 0.08)',
                  borderColor: 'rgba(0, 219, 231, 0.25)',
                  color: 'var(--teal, #00DBE7)',
                }}
                title="Open turn-by-turn walking directions in Google Maps"
              >
                <span>🧭 Map</span>
              </a>
            </div>

            {/* Thumbs Up / Down Feedback */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <button
                type="button"
                onClick={() => onFeedback?.(stop.id, stop.name, 1, stop.category, stop.is_niche)}
                style={{
                  background: feedbackState === 1 ? 'rgba(74, 222, 128, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                  border: `1px solid ${feedbackState === 1 ? '#4ade80' : 'rgba(255, 255, 255, 0.12)'}`,
                  color: feedbackState === 1 ? '#4ade80' : 'var(--text-muted)',
                  borderRadius: 8,
                  padding: '4px 8px',
                  fontSize: 13,
                  cursor: 'pointer',
                  transition: 'all 150ms',
                }}
                title="Great recommendation! Saves feedback to tune AI models"
              >
                👍
              </button>
              <button
                type="button"
                onClick={() => onFeedback?.(stop.id, stop.name, -1, stop.category, stop.is_niche)}
                style={{
                  background: feedbackState === -1 ? 'rgba(239, 68, 68, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                  border: `1px solid ${feedbackState === -1 ? '#ef4444' : 'rgba(255, 255, 255, 0.12)'}`,
                  color: feedbackState === -1 ? '#ef4444' : 'var(--text-muted)',
                  borderRadius: 8,
                  padding: '4px 8px',
                  fontSize: 13,
                  cursor: 'pointer',
                  transition: 'all 150ms',
                }}
                title="Not interested in this spot"
              >
                👎
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
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

interface Props {
  itinerary: Itinerary | null;
  isLoading: boolean;
  onStopAction?: (req: StopEditRequest) => void;
  onQuickEdit?: (instruction: string) => void;
}

export default function ItineraryView({ itinerary, isLoading, onStopAction, onQuickEdit }: Props) {
  const [activeDay, setActiveDay] = useState(0);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [isPackingModalOpen, setIsPackingModalOpen] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [viewMode, setViewMode] = useState<'cards' | 'timeline'>('cards');
  const [feedbackMap, setFeedbackMap] = useState<Record<string, 1 | -1>>({});
  const toast = useToast();
  
  // Drag and Drop state for current active day
  const [draggedIdx, setDraggedIdx] = useState<number | null>(null);
  const [dragOverIdx, setDragOverIdx] = useState<number | null>(null);
  const [localDays, setLocalDays] = useState<DayPlan[]>([]);

  useEffect(() => {
    if (itinerary?.days) {
      setLocalDays(itinerary.days);
    }
  }, [itinerary]);

  const handleDownloadPdf = async () => {
    if (!itinerary || isDownloadingPdf) return;
    setIsDownloadingPdf(true);
    toast.info('Generating high-fidelity PDF travel guide...', 'Exporting PDF');
    try {
      const res = await fetch('http://localhost:8000/export/pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(itinerary),
      });

      if (!res.ok) {
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
        toast.success('PDF travel guide downloaded successfully!', 'PDF Exported');
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
      toast.success('PDF travel guide downloaded successfully!', 'PDF Exported');
    } catch (err) {
      console.error('PDF download error:', err);
      toast.warning('Opening PDF in new tab...', 'Fallback Export');
      window.open(`http://localhost:8000/export/pdf/${itinerary.id}`, '_blank');
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handleFeedback = (stopId: string, stopName: string, rating: 1 | -1, category?: string, isNiche?: boolean) => {
    setFeedbackMap(prev => ({ ...prev, [stopId]: rating }));
    
    if (rating === 1) {
      toast.success(`Liked "${stopName}"! Saved to model fine-tuning dataset.`, 'Feedback Saved 👍');
    } else {
      toast.info(`Marked "${stopName}" as not preferred.`, 'Feedback Recorded 👎');
    }
    
    fetch('http://localhost:8000/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        itinerary_id: itinerary?.id,
        stop_id: stopId,
        stop_name: stopName,
        destination: itinerary?.trip_request?.destination || 'Destination',
        rating,
        category,
        is_niche: !!isNiche,
      }),
    }).catch(err => console.warn('Feedback submission failed:', err));
  };

  // Drag and Drop handlers
  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDraggedIdx(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (dragOverIdx !== index) {
      setDragOverIdx(index);
    }
  };

  const handleDrop = async (e: React.DragEvent, targetIndex: number) => {
    e.preventDefault();
    if (draggedIdx === null || draggedIdx === targetIndex || activeDay === -1) {
      setDraggedIdx(null);
      setDragOverIdx(null);
      return;
    }

    const currentDayPlan = localDays[activeDay];
    if (!currentDayPlan || !currentDayPlan.stops) return;

    const stops = [...currentDayPlan.stops];
    const [moved] = stops.splice(draggedIdx, 1);
    stops.splice(targetIndex, 0, moved);

    // Recalculate transit times optimistically
    const updatedStops = recalculateSequentialTransit(stops);
    const updatedDays = [...localDays];
    updatedDays[activeDay] = { ...currentDayPlan, stops: updatedStops };
    setLocalDays(updatedDays);

    setDraggedIdx(null);
    setDragOverIdx(null);
    toast.info('Transit times updated', 'Stops Reordered');

    // Sync to backend in background
    if (itinerary?.id) {
      fetch(`http://localhost:8000/plan/${itinerary.id}/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          day_number: currentDayPlan.day_number,
          stop_ids: updatedStops.map(s => s.id),
        }),
      }).catch(err => console.warn('Reorder sync error:', err));
    }
  };

  const handleDragEnd = () => {
    setDraggedIdx(null);
    setDragOverIdx(null);
  };

  if (isLoading) {
    return (
      <div className="itinerary-workspace-container" style={{ opacity: 0.9 }}>
        <div className="itinerary-workspace-header">
          <div>
            <div style={{ width: 220, height: 28, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 6, marginBottom: 8 }} />
            <div style={{ width: 340, height: 16, background: 'rgba(255, 255, 255, 0.04)', borderRadius: 4 }} />
          </div>
        </div>

        <div className="itinerary-dual-grid" style={{ marginTop: 24 }}>
          <div className="itinerary-timeline-pane" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {[1, 2, 3].map((n) => (
              <div
                key={n}
                style={{
                  background: 'rgba(13, 25, 44, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.06)',
                  borderRadius: 14,
                  padding: 16,
                  display: 'flex',
                  gap: 16,
                }}
              >
                <div style={{ width: 90, height: 90, borderRadius: 10, background: 'rgba(255, 255, 255, 0.06)' }} />
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <div style={{ width: '60%', height: 20, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 4 }} />
                  <div style={{ width: '90%', height: 14, background: 'rgba(255, 255, 255, 0.04)', borderRadius: 4 }} />
                  <div style={{ width: '40%', height: 14, background: 'rgba(255, 255, 255, 0.04)', borderRadius: 4 }} />
                </div>
              </div>
            ))}
          </div>
          <div className="itinerary-map-pane">
            <div style={{ width: '100%', height: 440, borderRadius: 16, background: 'rgba(4, 14, 31, 0.8)', border: '1px solid rgba(0, 219, 231, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ width: 36, height: 36, borderRadius: '50%', border: '3px solid var(--teal)', borderTopColor: 'transparent', animation: 'spin 1s linear infinite', margin: '0 auto 12px' }} />
                <span style={{ color: 'var(--teal)', fontSize: 13, fontFamily: 'var(--font-label)' }}>Plotting Multi-Agent Coordinates...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!itinerary) {
    return null;
  }

  const destination = itinerary.trip_request?.destination || 'Destination';
  const days = localDays.length > 0 ? localDays : (itinerary.days || []);
  
  const validActiveDay = (activeDay >= 0 && activeDay < days.length) ? activeDay : (activeDay === -1 ? -1 : 0);
  const currentDay: DayPlan | undefined = validActiveDay === -1 ? undefined : days[validActiveDay];
  const allStops = days.flatMap(d => d.stops || []);
  const displayedStops = validActiveDay === -1 ? allStops : (currentDay?.stops || []);
  const nicheTotal = allStops.filter(s => s.is_niche).length;

  // Calculate concrete timeline slots for active day
  const timelineData = calculateDayTimeline(displayedStops);

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
                Paced for <strong>{itinerary.trip_request?.pace || 'moderate'}</strong> speed · <strong>{itinerary.trip_request?.travel_style || 'balanced'}</strong> focus · Estimated Total: <strong style={{ color: 'var(--amber)', fontFamily: 'var(--font-mono)' }}><AnimatedCost value={itinerary.total_cost_estimate_usd} destination={destination} /></strong>
              </p>
            </div>

            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button
                onClick={() => setIsPackingModalOpen(true)}
                className="btn-primary-sm"
                style={{
                  padding: '9px 14px',
                  fontSize: 12.5,
                  background: 'rgba(255, 255, 255, 0.08)',
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                  color: '#fff',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.6)',
                }}
                title="Open customized smart weather packing checklist"
              >
                <span>🎒 Packing List</span>
              </button>
              <button
                onClick={() => {
                  const url = `http://localhost:8000/export/ical/${itinerary.id}`;
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `WanderAI-${destination}.ics`;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  toast.success('Calendar (.ics) downloaded. Open it to sync to Google/Apple Calendar!', 'Calendar Synced 📅');
                }}
                className="btn-primary-sm"
                style={{
                  padding: '9px 14px',
                  fontSize: 12.5,
                  background: 'rgba(0, 219, 231, 0.15)',
                  borderColor: '#00DBE7',
                  color: '#00DBE7',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.6)',
                }}
                title="Export .ics calendar file for Google / Apple / Outlook Calendar"
              >
                <span>📅 Calendar (.ics)</span>
              </button>
              <button
                onClick={handleDownloadPdf}
                disabled={isDownloadingPdf}
                className="btn-primary-sm"
                style={{ padding: '9px 14px', fontSize: 12.5, boxShadow: '0 4px 16px rgba(0,0,0,0.6)', cursor: isDownloadingPdf ? 'wait' : 'pointer' }}
                title="Download printable PDF travel guide"
              >
                <span>{isDownloadingPdf ? '⏳ PDF...' : '📄 PDF'}</span>
              </button>
              <button
                onClick={() => setIsShareModalOpen(true)}
                className="btn-primary-sm"
                style={{
                  padding: '9px 14px',
                  fontSize: 12.5,
                  background: 'rgba(232, 168, 56, 0.2)',
                  borderColor: '#E8A838',
                  color: '#E8A838',
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
              onClick={() => setIsPackingModalOpen(true)}
              className="btn-primary-sm"
              style={{ padding: '8px 12px', fontSize: 12.5 }}
              title="Open customized smart weather packing checklist"
            >
              <span>🎒 Packing List</span>
            </button>
            <button
              onClick={() => {
                const url = `http://localhost:8000/export/ical/${itinerary.id}`;
                const a = document.createElement('a');
                a.href = url;
                a.download = `WanderAI-${destination}.ics`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
              }}
              className="btn-primary-sm"
              style={{
                padding: '8px 12px',
                fontSize: 12.5,
                background: 'rgba(0, 219, 231, 0.15)',
                borderColor: '#00DBE7',
                color: '#00DBE7',
              }}
              title="Export .ics calendar file"
            >
              <span>📅 Calendar (.ics)</span>
            </button>
            <button
              onClick={handleDownloadPdf}
              disabled={isDownloadingPdf}
              className="btn-primary-sm"
              style={{ padding: '8px 12px', fontSize: 12.5, cursor: isDownloadingPdf ? 'wait' : 'pointer' }}
              title="Download printable PDF travel guide"
            >
              <span>{isDownloadingPdf ? '⏳ PDF...' : '📄 PDF'}</span>
            </button>
            <button
              onClick={() => setIsShareModalOpen(true)}
              className="btn-primary-sm"
              style={{
                padding: '8px 12px',
                fontSize: 12.5,
                background: 'rgba(232, 168, 56, 0.15)',
                borderColor: '#E8A838',
                color: '#E8A838',
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

      {/* Smart Packing List Modal */}
      <PackingListModal
        isOpen={isPackingModalOpen}
        onClose={() => setIsPackingModalOpen(false)}
        itinerary={itinerary}
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

      {/* Day Selector Navigation & View Switcher Strip */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginBottom: 20 }}>
        <div className="day-tabs-strip" style={{ marginBottom: 0 }}>
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

        {/* View Mode Toggle: Cards vs Timeline Grid */}
        <div style={{ display: 'flex', background: 'rgba(4, 14, 31, 0.7)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: 'var(--radius-full)', padding: 3 }}>
          <button
            type="button"
            onClick={() => setViewMode('cards')}
            style={{
              background: viewMode === 'cards' ? 'var(--amber)' : 'transparent',
              color: viewMode === 'cards' ? '#040e1f' : 'var(--text-muted)',
              border: 'none',
              borderRadius: 'var(--radius-full)',
              padding: '4px 12px',
              fontSize: 12,
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'all 150ms',
            }}
          >
            🗂️ Cards
          </button>
          <button
            type="button"
            onClick={() => setViewMode('timeline')}
            style={{
              background: viewMode === 'timeline' ? 'var(--teal)' : 'transparent',
              color: viewMode === 'timeline' ? '#040e1f' : 'var(--text-muted)',
              border: 'none',
              borderRadius: 'var(--radius-full)',
              padding: '4px 12px',
              fontSize: 12,
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'all 150ms',
            }}
          >
            ⏱️ Timeline
          </button>
        </div>
      </div>

      {/* Side-by-Side Dual-Pane Grid: Timeline/Cards (Left) + Interactive Map (Right) */}
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

          {/* Drag and Drop instruction banner when in single day mode */}
          {validActiveDay !== -1 && displayedStops.length > 1 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11.5, color: 'var(--text-muted)', margin: '8px 4px 12px' }}>
              <span>⋮⋮</span>
              <span>Drag any stop card to reorder your route (transit times recalculate automatically)</span>
            </div>
          )}

          {/* Sequential Stops */}
          <div className="stops-timeline-list">
            {displayedStops.map((stop, idx) => {
              const stopDayNumber = validActiveDay === -1
                ? (days.find(d => d.stops?.some(s => s.id === stop.id))?.day_number || 1)
                : (currentDay?.day_number || 1);

              const timeSlot = timelineData[idx]?.timeSlot;
              const transitBefore = timelineData[idx]?.transitBefore;

              return (
                <StopCard
                  key={stop.id || idx}
                  stop={stop}
                  index={idx}
                  destination={destination}
                  dayNumber={stopDayNumber}
                  itineraryId={itinerary.id}
                  timeSlot={timeSlot}
                  transitBefore={transitBefore}
                  onStopAction={onStopAction}
                  onFeedback={handleFeedback}
                  feedbackState={feedbackMap[stop.id]}
                  isDraggable={validActiveDay !== -1}
                  onDragStart={handleDragStart}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                  onDragEnd={handleDragEnd}
                  isDragOver={dragOverIdx === idx && draggedIdx !== idx}
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
