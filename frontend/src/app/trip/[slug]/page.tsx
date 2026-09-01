'use client';

import { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { Itinerary, DayPlan, Stop } from '@/types';
import { formatCost, formatTotalCost } from '@/utils/currency';
import MapView from '@/components/MapView';
import ShareModal from '@/components/ShareModal';

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

function PublicStopCard({ stop, index, destination }: { stop: Stop; index: number; destination: string }) {
  const [imgError, setImgError] = useState(false);
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
              <div className="niche-badge">
                💎 HIDDEN GEM
              </div>
            )}
          </div>

          {stop.narration ? (
            <p className="stop-narration">"{stop.narration}"</p>
          ) : (
            <p className="stop-narration" style={{ fontStyle: 'normal' }}>
              {stop.description || 'Curated stop.'}
            </p>
          )}

          <div className="stop-meta">
            <span className="stop-category-pill">{stop.category || 'attraction'}</span>
            <span style={{ color: 'var(--text-muted)' }}>⏱️ {stop.duration_minutes || 60} min</span>
            {stop.estimated_cost_usd !== undefined && (
              <span className="stop-cost">{formatCost(stop.estimated_cost_usd, destination)}</span>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default function SharedTripPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeDay, setActiveDay] = useState(0);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  useEffect(() => {
    async function fetchTrip() {
      try {
        setLoading(true);
        // 1. Try backend /share/{slug} endpoint
        const res = await fetch(`http://localhost:8000/share/${slug}`);
        if (res.ok) {
          const data = await res.json();
          setItinerary(data);
          setLoading(false);
          return;
        }

        // 2. Try backend /history/{slug} endpoint
        const histRes = await fetch(`http://localhost:8000/history/${slug}`);
        if (histRes.ok) {
          const data = await histRes.json();
          setItinerary(data);
          setLoading(false);
          return;
        }

        // 3. Fallback: check localStorage for saved trip
        if (typeof window !== 'undefined') {
          const raw = localStorage.getItem('wanderai_saved_trips');
          if (raw) {
            const list = JSON.parse(raw);
            const found = list.find((item: any) => item.id === slug || item.id?.startsWith(slug));
            if (found && found.itinerary) {
              setItinerary(found.itinerary);
              setLoading(false);
              return;
            }
          }
        }

        setError('Trip not found or link has expired.');
      } catch (err: any) {
        console.error('Failed to fetch shared trip:', err);
        setError('Could not load shared itinerary.');
      } finally {
        setLoading(false);
      }
    }

    fetchTrip();
  }, [slug]);

  const handleDownloadPdf = async () => {
    if (!itinerary || isDownloadingPdf) return;
    setIsDownloadingPdf(true);
    try {
      const res = await fetch('http://localhost:8000/export/pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(itinerary),
      });

      if (!res.ok) throw new Error('PDF export failed');
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
      window.open(`http://localhost:8000/export/pdf/${itinerary.id}`, '_blank');
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: '#040e1f', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: 44, height: 44, margin: '0 auto 16px', borderRadius: '50%', border: '3px solid rgba(0, 219, 231, 0.2)', borderTopColor: '#00DBE7', animation: 'spin 1s linear infinite' }} />
          <div style={{ fontFamily: 'Playfair Display, serif', fontSize: '20px', color: '#00DBE7' }}>
            Loading Shared Itinerary...
          </div>
        </div>
      </div>
    );
  }

  if (error || !itinerary) {
    return (
      <div style={{ minHeight: '100vh', background: '#040e1f', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', padding: '24px' }}>
        <div style={{ textAlign: 'center', maxWidth: '440px' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🗺️</div>
          <h2 style={{ fontFamily: 'Playfair Display, serif', fontSize: '24px', marginBottom: '8px' }}>
            {error || 'Itinerary Not Found'}
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '24px' }}>
            This travel itinerary link may be invalid or the trip has been removed.
          </p>
          <Link
            href="/"
            className="btn-primary-sm"
            style={{ display: 'inline-flex', padding: '12px 24px', fontSize: '15px', textDecoration: 'none' }}
          >
            ✨ Plan Your Own Trip on WanderAI
          </Link>
        </div>
      </div>
    );
  }

  const dest = itinerary.trip_request?.destination || 'Destination';
  const days = itinerary.days || [];
  const validActiveDay = (activeDay >= 0 && activeDay < days.length) ? activeDay : (activeDay === -1 ? -1 : 0);
  const currentDay = validActiveDay === -1 ? undefined : days[validActiveDay];
  const allStops = days.flatMap(d => d.stops || []);
  const displayedStops = validActiveDay === -1 ? allStops : (currentDay?.stops || []);
  const nicheTotal = allStops.filter(s => s.is_niche).length;

  return (
    <div style={{ minHeight: '100vh', background: '#040e1f', color: '#ffffff', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation Bar */}
      <header
        style={{
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          background: 'rgba(4, 14, 31, 0.85)',
          backdropFilter: 'blur(12px)',
          position: 'sticky',
          top: 0,
          zIndex: 100,
          padding: '14px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Link href="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ fontFamily: 'Playfair Display, serif', fontSize: '22px', fontWeight: 800, color: '#00DBE7' }}>
            Wander<span style={{ color: '#ffffff' }}>AI</span>
          </div>
          <span style={{ fontSize: '11px', background: 'rgba(0, 219, 231, 0.15)', color: '#00DBE7', padding: '2px 8px', borderRadius: '12px', fontWeight: 600 }}>
            Shared Trip
          </span>
        </Link>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            onClick={handleDownloadPdf}
            disabled={isDownloadingPdf}
            className="btn-primary-sm"
            style={{ padding: '8px 14px', fontSize: '13px' }}
          >
            <span>{isDownloadingPdf ? '⏳ PDF...' : '📄 PDF'}</span>
          </button>
          <button
            onClick={() => setIsShareModalOpen(true)}
            className="btn-primary-sm"
            style={{ padding: '8px 14px', fontSize: '13px', background: 'rgba(0, 219, 231, 0.2)', borderColor: '#00DBE7', color: '#00DBE7' }}
          >
            <span>🔗 Share</span>
          </button>
          <Link
            href="/"
            className="btn-primary-sm"
            style={{ padding: '8px 18px', fontSize: '13px', textDecoration: 'none' }}
          >
            <span>✨ Plan a Trip</span>
          </Link>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '24px', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
        <div className="itinerary-workspace-container">
          {/* Destination Hero Banner */}
          <div
            className="itinerary-cover-banner"
            style={itinerary.cover_image_url ? { backgroundImage: `url(${itinerary.cover_image_url})` } : {}}
          >
            <div className="itinerary-cover-content">
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  <h1 className="itinerary-destination-title" style={{ textShadow: '0 2px 12px rgba(0,0,0,0.8)' }}>
                    {itinerary.trip_request?.num_days || days.length}-Day Journey to {dest}
                  </h1>
                  {nicheTotal > 0 && (
                    <span className="niche-badge" style={{ fontSize: 11, padding: '4px 12px' }}>
                      💎 {nicheTotal} Community Hidden Gems
                    </span>
                  )}
                </div>
                <p style={{ fontSize: 13, color: '#d8e3fb', marginTop: 6, textShadow: '0 1px 4px rgba(0,0,0,0.8)' }}>
                  Paced for <strong>{itinerary.trip_request?.pace || 'moderate'}</strong> speed · <strong>{itinerary.trip_request?.travel_style || 'balanced'}</strong> focus · Estimated Total: <strong style={{ color: 'var(--amber)' }}>{formatTotalCost(itinerary.total_cost_estimate_usd, dest)}</strong>
                </p>
              </div>
            </div>
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
              <span className="day-tab-num">All</span>
              <span className="day-tab-theme">All Stops ({allStops.length})</span>
            </button>
          </div>

          {/* Dual Column Layout: Left Stops / Right Map */}
          <div className="itinerary-grid">
            {/* Left Column: Stops */}
            <div className="itinerary-stops-col">
              {currentDay && (
                <div className="day-summary-card">
                  <div className="day-summary-top">
                    <span className="day-pill">Day {currentDay.day_number}</span>
                    {currentDay.day_cost_estimate_usd !== undefined && (
                      <span className="day-cost-badge">
                        Est. {formatCost(currentDay.day_cost_estimate_usd, dest)}
                      </span>
                    )}
                  </div>
                  <h3 className="day-theme-title">
                    {currentDay.theme || `Day ${currentDay.day_number}`}
                  </h3>
                  {currentDay.weather_note && (
                    <div className="weather-badge">
                      {currentDay.weather_note}
                    </div>
                  )}
                </div>
              )}

              <div className="stops-timeline">
                {displayedStops.map((stop, index) => (
                  <PublicStopCard
                    key={stop.id || `${stop.name}-${index}`}
                    stop={stop}
                    index={index}
                    destination={dest}
                  />
                ))}
              </div>
            </div>

            {/* Right Column: Interactive Map */}
            <div className="itinerary-map-col">
              <div className="itinerary-map-sticky">
                <MapView stops={displayedStops} activeDay={validActiveDay} />
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Share Modal Dialog */}
      <ShareModal
        isOpen={isShareModalOpen}
        onClose={() => setIsShareModalOpen(false)}
        itinerary={itinerary}
        onDownloadPdf={handleDownloadPdf}
        isDownloadingPdf={isDownloadingPdf}
      />
    </div>
  );
}
