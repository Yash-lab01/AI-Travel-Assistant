'use client';

import React, { useEffect, useState } from 'react';
import { Itinerary, TripHistoryRecord } from '@/types';
import { formatTotalCost } from '@/utils/currency';

interface TripHistoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTrip: (itinerary: Itinerary) => void;
  currentItineraryId?: string | null;
  onHistoryUpdated?: () => void;
}

const STORAGE_KEY = 'wanderai_trip_history';

function getRelativeTimeString(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffSec < 60) return 'Just now';
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    if (diffSec < 172800) return 'Yesterday';
    if (diffSec < 604800) return `${Math.floor(diffSec / 86400)}d ago`;

    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return 'Recently';
  }
}

export default function TripHistoryPanel({
  isOpen,
  onClose,
  onSelectTrip,
  currentItineraryId,
  onHistoryUpdated,
}: TripHistoryPanelProps) {
  const [historyRecords, setHistoryRecords] = useState<TripHistoryRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingTripId, setLoadingTripId] = useState<string | null>(null);

  // Load history from localStorage and sync with backend
  const loadHistory = async () => {
    setIsLoading(true);
    let localTrips: TripHistoryRecord[] = [];
    
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        localTrips = JSON.parse(stored);
      }
    } catch (e) {
      console.warn('Failed to parse localStorage trip history', e);
    }

    // If local storage has items, display them first
    if (localTrips.length > 0) {
      setHistoryRecords(localTrips);
      setIsLoading(false);
      return;
    }

    // Otherwise fetch from backend SQLite /history
    try {
      const res = await fetch('http://localhost:8000/history');
      if (res.ok) {
        const backendTrips: TripHistoryRecord[] = await res.json();
        setHistoryRecords(backendTrips);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(backendTrips));
      }
    } catch (e) {
      console.warn('Failed to fetch /history from backend', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadHistory();
    }
  }, [isOpen]);

  // Handle trip selection / restoration
  const handleSelect = async (record: TripHistoryRecord) => {
    setLoadingTripId(record.id);

    try {
      // 1. If full itinerary object exists in record, use it immediately
      if (record.itinerary && record.itinerary.days && record.itinerary.days.length > 0) {
        onSelectTrip(record.itinerary);
        onClose();
        return;
      }

      // 2. Fetch full itinerary from backend by ID
      const res = await fetch(`http://localhost:8000/history/${record.id}`);
      if (res.ok) {
        const fullItinerary: Itinerary = await res.json();
        onSelectTrip(fullItinerary);
        onClose();
      } else {
        alert('Could not retrieve full itinerary for this trip.');
      }
    } catch (e) {
      console.error('Error loading trip from history:', e);
      alert('Error loading saved trip.');
    } finally {
      setLoadingTripId(null);
    }
  };

  // Delete a trip
  const handleDelete = async (e: React.MouseEvent, tripId: string) => {
    e.stopPropagation();

    // 1. Remove from local state
    const updated = historyRecords.filter((t) => t.id !== tripId);
    setHistoryRecords(updated);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (err) {
      console.warn('Error updating localStorage:', err);
    }

    // 2. Notify parent to update count badge
    if (onHistoryUpdated) {
      onHistoryUpdated();
    }

    // 3. Delete from backend in background
    try {
      await fetch(`http://localhost:8000/history/${tripId}`, { method: 'DELETE' });
    } catch (err) {
      console.warn('Error deleting from backend /history:', err);
    }
  };

  // Clear all history
  const handleClearAll = async () => {
    if (!confirm('Are you sure you want to clear all saved trip history?')) return;

    const idsToDelete = historyRecords.map((r) => r.id);
    setHistoryRecords([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (err) {
      console.warn('Error clearing localStorage:', err);
    }

    if (onHistoryUpdated) {
      onHistoryUpdated();
    }

    // Delete all from backend
    for (const id of idsToDelete) {
      try {
        await fetch(`http://localhost:8000/history/${id}`, { method: 'DELETE' });
      } catch {
        // ignore
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="history-modal-overlay" onClick={onClose}>
      <aside
        className="history-drawer"
        onClick={(e) => e.stopPropagation()}
        aria-label="Saved Trip History"
      >
        {/* Header */}
        <div className="history-header">
          <div className="history-title-group">
            <div className="history-icon-badge">🗂️</div>
            <div>
              <h2 className="history-title">Trip History</h2>
              <p className="history-subtitle">
                {historyRecords.length} {historyRecords.length === 1 ? 'journey' : 'journeys'} saved
              </p>
            </div>
          </div>
          <button
            type="button"
            className="history-close-btn"
            onClick={onClose}
            aria-label="Close history panel"
          >
            ✕
          </button>
        </div>

        {/* Content Body */}
        <div className="history-body">
          {isLoading ? (
            <div className="history-loading">
              <span className="live-dot" />
              <span>Loading saved journeys...</span>
            </div>
          ) : historyRecords.length === 0 ? (
            <div className="history-empty-state">
              <div className="history-empty-icon" style={{ fontSize: 44, animation: 'float 3s ease-in-out infinite' }}>🧭</div>
              <h3 className="history-empty-title" style={{ fontFamily: 'var(--font-heading)', fontSize: 18, color: '#fff', margin: '8px 0' }}>
                No Saved Journeys Yet
              </h3>
              <p className="history-empty-desc" style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 16 }}>
                Every itinerary you design is automatically backed up here for seamless access across your sessions.
              </p>
              <button
                type="button"
                className="btn-primary-sm"
                onClick={onClose}
                style={{ margin: '0 auto', fontSize: 12.5, padding: '7px 16px' }}
              >
                <span>✨ Plan Your First Journey</span>
              </button>
            </div>
          ) : (
            <div className="history-cards-list">
              {historyRecords.map((record) => {
                const isActive = record.id === currentItineraryId;
                const isItemLoading = loadingTripId === record.id;
                const coverImage = record.cover_image_url || record.itinerary?.cover_image_url;

                return (
                  <div
                    key={record.id}
                    className={`history-trip-card ${isActive ? 'active' : ''}`}
                    onClick={() => handleSelect(record)}
                  >
                    {/* Thumbnail Image */}
                    <div
                      className="history-card-thumb"
                      style={{
                        backgroundImage: coverImage ? `url(${coverImage})` : undefined,
                      }}
                    >
                      {!coverImage && <span style={{ fontSize: 24 }}>🗺️</span>}
                      {isActive && (
                        <div className="history-active-chip">
                          <span className="live-dot" /> Active
                        </div>
                      )}
                    </div>

                    {/* Card Info */}
                    <div className="history-card-content">
                      <div className="history-card-top-row">
                        <h4 className="history-card-dest">{record.destination}</h4>
                        <button
                          type="button"
                          className="history-delete-btn"
                          title="Delete saved trip"
                          onClick={(e) => handleDelete(e, record.id)}
                        >
                          🗑️
                        </button>
                      </div>

                      <div className="history-card-meta">
                        <span className="history-meta-pill">{record.num_days} {record.num_days === 1 ? 'Day' : 'Days'}</span>
                        {record.total_cost_usd !== undefined && record.total_cost_usd > 0 && (
                          <span className="history-meta-cost">
                            {formatTotalCost(record.total_cost_usd, record.destination)}
                          </span>
                        )}
                        <span className="history-meta-time">
                          {getRelativeTimeString(record.created_at)}
                        </span>
                      </div>

                      <div className="history-card-actions">
                        <button
                          type="button"
                          className="history-load-btn"
                          disabled={isItemLoading}
                        >
                          {isItemLoading ? 'Loading...' : isActive ? 'Viewing Plan ✓' : 'Load Itinerary ➔'}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        {historyRecords.length > 0 && (
          <div className="history-footer">
            <span className="history-storage-note">💾 Saved locally & on server</span>
            <button
              type="button"
              className="history-clear-all-btn"
              onClick={handleClearAll}
            >
              Clear All History
            </button>
          </div>
        )}
      </aside>
    </div>
  );
}
