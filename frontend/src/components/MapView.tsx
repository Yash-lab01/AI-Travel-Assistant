'use client';

import { useEffect, useRef } from 'react';
import { Stop } from '@/types';

interface Props {
  stops: Stop[];
  activeDay: number;
}

declare global {
  interface Window {
    mapboxgl: typeof import('mapbox-gl');
  }
}

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '';

// Category colours matching the design system
const MARKER_COLORS: Record<string, string> = {
  attraction: '#E8A838',  // amber — popular
  museum:     '#E8A838',
  restaurant: '#10B981',  // emerald — food
  park:       '#10B981',
  viewpoint:  '#00DBE7',  // teal — scenic
  market:     '#a78bfa',  // purple — shopping
  beach:      '#00DBE7',
  default:    '#E8A838',
};

function createMarkerEl(stop: Stop, index: number): HTMLElement {
  const color = stop.is_niche
    ? '#00DBE7'  // teal for niche gems
    : (MARKER_COLORS[stop.category] ?? MARKER_COLORS.default);

  const el = document.createElement('div');
  el.style.cssText = `
    width: 32px;
    height: 32px;
    border-radius: 50% 50% 50% 0;
    background: ${color};
    border: 2px solid rgba(255,255,255,0.3);
    transform: rotate(-45deg);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.4)${stop.is_niche ? `, 0 0 16px ${color}80` : ''};
    transition: transform 200ms, box-shadow 200ms;
  `;

  const label = document.createElement('div');
  label.style.cssText = `
    transform: rotate(45deg);
    color: #0a0e1a;
    font-family: 'Sora', sans-serif;
    font-size: 11px;
    font-weight: 700;
    line-height: 1;
  `;
  label.textContent = String(index + 1);
  el.appendChild(label);

  el.addEventListener('mouseenter', () => {
    el.style.transform = 'rotate(-45deg) scale(1.2)';
    el.style.boxShadow = `0 4px 20px rgba(0,0,0,0.5)${stop.is_niche ? `, 0 0 24px ${color}` : ''}`;
    el.style.zIndex = '10';
  });
  el.addEventListener('mouseleave', () => {
    el.style.transform = 'rotate(-45deg) scale(1)';
    el.style.boxShadow = `0 2px 12px rgba(0,0,0,0.4)${stop.is_niche ? `, 0 0 16px ${color}80` : ''}`;
    el.style.zIndex = '';
  });

  return el;
}

export default function MapView({ stops, activeDay }: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<import('mapbox-gl').Map | null>(null);
  const markersRef = useRef<import('mapbox-gl').Marker[]>([]);

  useEffect(() => {
    if (!mapRef.current || !MAPBOX_TOKEN) return;

    // Dynamically load Mapbox GL JS
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://api.mapbox.com/mapbox-gl-js/v3.4.0/mapbox-gl.css';
    document.head.appendChild(link);

    const script = document.createElement('script');
    script.src = 'https://api.mapbox.com/mapbox-gl-js/v3.4.0/mapbox-gl.js';
    script.async = true;
    script.onload = initMap;
    document.head.appendChild(script);

    return () => {
      mapInstanceRef.current?.remove();
      link.remove();
      script.remove();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function initMap() {
    if (!mapRef.current || !window.mapboxgl) return;
    window.mapboxgl.accessToken = MAPBOX_TOKEN;

    const map = new window.mapboxgl.Map({
      container: mapRef.current,
      style: 'mapbox://styles/mapbox/navigation-night-v1',
      center: [0, 20],
      zoom: 2,
      projection: 'mercator',
    });

    map.addControl(new window.mapboxgl.NavigationControl(), 'top-right');
    mapInstanceRef.current = map;

    map.on('load', () => updateMarkers());
  }

  function updateMarkers() {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clear old markers
    markersRef.current.forEach(m => m.remove());
    markersRef.current = [];

    if (!stops.length) return;

    // Add new markers
    stops.forEach((stop, i) => {
      if (!stop.lat || !stop.lon) return;
      const el = createMarkerEl(stop, i);

      const popup = new window.mapboxgl.Popup({
        offset: 25,
        closeButton: false,
        className: 'wander-popup',
      }).setHTML(`
        <div style="
          background: rgba(21,32,49,0.95);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 12px;
          padding: 12px;
          max-width: 220px;
          font-family: Outfit, sans-serif;
          color: #d8e3fb;
        ">
          ${stop.is_niche ? '<div style="color:#00DBE7;font-size:10px;font-weight:700;letter-spacing:0.08em;margin-bottom:6px">💎 HIDDEN GEM</div>' : ''}
          <div style="font-family:\'Playfair Display\',serif;font-size:15px;font-weight:600;margin-bottom:4px">${stop.name}</div>
          <div style="font-size:12px;color:#909096;text-transform:capitalize;margin-bottom:8px">${stop.category} · ${stop.duration_minutes}min</div>
          ${stop.estimated_cost_usd !== undefined ? `<div style="font-size:12px;color:#FFBF00">$${stop.estimated_cost_usd} est.</div>` : ''}
        </div>
      `);

      const marker = new window.mapboxgl.Marker({ element: el })
        .setLngLat([stop.lon, stop.lat])
        .setPopup(popup)
        .addTo(map);

      markersRef.current.push(marker);
    });

    // Fit map to all markers
    if (stops.length === 1) {
      map.flyTo({ center: [stops[0].lon, stops[0].lat], zoom: 14, duration: 1500 });
    } else {
      const lons = stops.map(s => s.lon).filter(Boolean) as number[];
      const lats = stops.map(s => s.lat).filter(Boolean) as number[];
      map.fitBounds(
        [[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]],
        { padding: 60, duration: 1500 }
      );
    }
  }

  useEffect(() => {
    if (mapInstanceRef.current?.loaded()) {
      updateMarkers();
    }
  }, [stops, activeDay]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!MAPBOX_TOKEN) {
    return (
      <div style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        background: 'rgba(21,32,49,0.5)',
        borderTop: '1px solid var(--glass-border)',
        color: 'var(--text-muted)',
        fontSize: 13,
        fontFamily: 'var(--font-label)',
        padding: 24,
        textAlign: 'center',
      }}>
        <span style={{ fontSize: 32 }}>🗺️</span>
        <span>Add <code style={{ color: 'var(--amber)', background: 'rgba(255,191,0,0.1)', padding: '2px 6px', borderRadius: 4 }}>NEXT_PUBLIC_MAPBOX_TOKEN</code> to <code>.env</code> to enable the map.</span>
        <a
          href="https://account.mapbox.com/access-tokens/"
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: 'var(--teal)', fontSize: 12 }}
        >
          Get a free Mapbox token →
        </a>
      </div>
    );
  }

  return (
    <div
      ref={mapRef}
      style={{ width: '100%', height: '100%' }}
    />
  );
}
