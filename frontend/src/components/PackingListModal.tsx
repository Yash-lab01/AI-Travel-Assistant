'use client';

import { useEffect, useState } from 'react';
import { Itinerary, PackingListResponse } from '@/types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  itinerary: Itinerary | null;
}

export default function PackingListModal({ isOpen, onClose, itinerary }: Props) {
  const [packingData, setPackingData] = useState<PackingListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [copied, setCopied] = useState(false);

  const itineraryId = itinerary?.id || 'default';
  const storageKey = `wanderai_packing_${itineraryId}`;

  // Load saved check state
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(storageKey);
        if (saved) {
          setCheckedItems(JSON.parse(saved));
        }
      } catch {}
    }
  }, [storageKey]);

  // Fetch or generate packing list when modal opens
  useEffect(() => {
    if (!isOpen || !itinerary) return;

    // Check if cached data exists in sessionStorage
    const cacheKey = `wanderai_packing_data_${itineraryId}`;
    const cached = sessionStorage.getItem(cacheKey);
    if (cached) {
      try {
        setPackingData(JSON.parse(cached));
        return;
      } catch {}
    }

    setIsLoading(true);
    fetch('http://localhost:8000/trip/packing-list', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(itinerary),
    })
      .then((res) => res.json())
      .then((data: PackingListResponse) => {
        setPackingData(data);
        sessionStorage.setItem(cacheKey, JSON.stringify(data));
      })
      .catch((err) => {
        console.warn('Failed to load packing list:', err);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [isOpen, itinerary, itineraryId]);

  if (!isOpen || !itinerary) return null;

  const toggleItem = (itemKey: string) => {
    setCheckedItems((prev) => {
      const updated = { ...prev, [itemKey]: !prev[itemKey] };
      try {
        localStorage.setItem(storageKey, JSON.stringify(updated));
      } catch {}
      return updated;
    });
  };

  const categories = packingData?.categories || [];
  const allItems = categories.flatMap((c) => c.items.map((it) => ({ ...it, categoryName: c.name, categoryIcon: c.icon })));
  const totalCount = allItems.length;
  const packedCount = allItems.filter((it) => checkedItems[it.item]).length;
  const progressPct = totalCount > 0 ? Math.round((packedCount / totalCount) * 100) : 0;

  const displayedCategories = activeCategory === 'all'
    ? categories
    : categories.filter((c) => c.name.toLowerCase().includes(activeCategory.toLowerCase()) || activeCategory.toLowerCase().includes(c.name.toLowerCase()));

  const handleCopyChecklist = () => {
    if (!packingData) return;
    const lines = [`🎒 WanderAI Packing Checklist — ${itinerary.trip_request?.destination || 'Trip'}\n`];
    if (packingData.weather_summary) {
      lines.push(`☀️ Weather Note: ${packingData.weather_summary}\n`);
    }
    categories.forEach((cat) => {
      lines.push(`\n${cat.icon} ${cat.name}:`);
      cat.items.forEach((it) => {
        const checkMark = checkedItems[it.item] ? '[x]' : '[ ]';
        lines.push(`  ${checkMark} ${it.item}${it.reason ? ` (${it.reason})` : ''}`);
      });
    });
    navigator.clipboard.writeText(lines.join('\n'));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="share-modal-backdrop" onClick={onClose}>
      <div
        className="share-modal-card"
        style={{ maxWidth: 640, maxHeight: '88vh', display: 'flex', flexDirection: 'column' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 24 }}>🎒</span>
              <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 20, color: '#fff', margin: 0 }}>
                Smart Packing Checklist
              </h3>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
              Activity- & weather-aware packing guide for {itinerary.trip_request?.destination || 'your destination'}.
            </p>
          </div>
          <button
            onClick={onClose}
            className="share-modal-close"
            style={{ fontSize: 18, padding: '4px 8px' }}
          >
            ✕
          </button>
        </div>

        {/* Weather Banner */}
        {packingData?.weather_summary && (
          <div
            style={{
              background: 'rgba(0, 219, 231, 0.08)',
              border: '1px solid rgba(0, 219, 231, 0.25)',
              borderRadius: 'var(--radius-md, 8px)',
              padding: '8px 12px',
              fontSize: 12.5,
              color: '#d8f6ff',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginBottom: 16,
            }}
          >
            <span>☀️</span>
            <span>{packingData.weather_summary}</span>
          </div>
        )}

        {/* Progress Bar */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>
            <span>Packing Progress</span>
            <span style={{ color: progressPct === 100 ? '#4ade80' : 'var(--amber)', fontWeight: 700 }}>
              {packedCount} / {totalCount} Packed ({progressPct}%)
            </span>
          </div>
          <div style={{ width: '100%', height: 6, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 9999, overflow: 'hidden' }}>
            <div
              style={{
                width: `${progressPct}%`,
                height: '100%',
                background: progressPct === 100 ? '#4ade80' : 'linear-gradient(90deg, #f59e0b, #00dbe7)',
                transition: 'width 300ms ease-out',
              }}
            />
          </div>
        </div>

        {/* Category Pills */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
          <button
            type="button"
            onClick={() => setActiveCategory('all')}
            style={{
              padding: '4px 10px',
              fontSize: 11.5,
              borderRadius: 9999,
              border: '1px solid',
              borderColor: activeCategory === 'all' ? 'var(--amber)' : 'rgba(255, 255, 255, 0.1)',
              background: activeCategory === 'all' ? 'rgba(245, 158, 11, 0.15)' : 'transparent',
              color: activeCategory === 'all' ? 'var(--amber)' : 'var(--text-muted)',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            All Items ({totalCount})
          </button>
          {categories.map((c) => (
            <button
              key={c.name}
              type="button"
              onClick={() => setActiveCategory(c.name)}
              style={{
                padding: '4px 10px',
                fontSize: 11.5,
                borderRadius: 9999,
                border: '1px solid',
                borderColor: activeCategory === c.name ? 'var(--amber)' : 'rgba(255, 255, 255, 0.1)',
                background: activeCategory === c.name ? 'rgba(245, 158, 11, 0.15)' : 'transparent',
                color: activeCategory === c.name ? 'var(--amber)' : 'var(--text-muted)',
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              {c.icon} {c.name}
            </button>
          ))}
        </div>

        {/* Scrollable Checklist Area */}
        <div style={{ flex: 1, overflowY: 'auto', paddingRight: 4, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
              <div style={{ width: 32, height: 32, borderRadius: '50%', border: '2px solid var(--amber)', borderTopColor: 'transparent', animation: 'spin 1s linear infinite', margin: '0 auto 12px' }} />
              <span>Analyzing destination climate, voltages & activity gear...</span>
            </div>
          ) : (
            displayedCategories.map((cat) => (
              <div key={cat.name} style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)', borderRadius: 10, padding: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 700, color: '#fff', marginBottom: 10, fontFamily: 'var(--font-label)' }}>
                  <span>{cat.icon}</span>
                  <span>{cat.name}</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {cat.items.map((it) => {
                    const isChecked = !!checkedItems[it.item];
                    return (
                      <label
                        key={it.item}
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 10,
                          cursor: 'pointer',
                          padding: '6px 8px',
                          borderRadius: 6,
                          background: isChecked ? 'rgba(74, 222, 128, 0.05)' : 'transparent',
                          transition: 'all 150ms',
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => toggleItem(it.item)}
                          style={{
                            marginTop: 3,
                            accentColor: '#f59e0b',
                            width: 16,
                            height: 16,
                            cursor: 'pointer',
                          }}
                        />
                        <div style={{ flex: 1 }}>
                          <div
                            style={{
                              fontSize: 13,
                              color: isChecked ? '#94a3b8' : '#f1f5f9',
                              textDecoration: isChecked ? 'line-through' : 'none',
                              fontWeight: 500,
                            }}
                          >
                            {it.item}
                            {it.is_essential && (
                              <span
                                style={{
                                  marginLeft: 6,
                                  fontSize: 10,
                                  color: '#f59e0b',
                                  background: 'rgba(245, 158, 11, 0.15)',
                                  padding: '1px 6px',
                                  borderRadius: 4,
                                  fontWeight: 700,
                                }}
                              >
                                ESSENTIAL
                              </span>
                            )}
                          </div>
                          {it.reason && (
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                              {it.reason}
                            </div>
                          )}
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer Actions */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16, paddingTop: 12, borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <button
            type="button"
            onClick={() => {
              setCheckedItems({});
              try {
                localStorage.removeItem(storageKey);
              } catch {}
            }}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: 12,
              cursor: 'pointer',
              textDecoration: 'underline',
            }}
          >
            Reset checklist
          </button>

          <div style={{ display: 'flex', gap: 8 }}>
            <button
              type="button"
              onClick={handleCopyChecklist}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                color: '#fff',
                padding: '7px 14px',
                borderRadius: 8,
                fontSize: 12.5,
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {copied ? '✅ Copied!' : '📋 Copy Text'}
            </button>
            <button
              type="button"
              onClick={onClose}
              style={{
                background: 'var(--amber)',
                border: 'none',
                color: '#040e1f',
                padding: '7px 16px',
                borderRadius: 8,
                fontSize: 12.5,
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
