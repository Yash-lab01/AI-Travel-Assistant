'use client';

import { useEffect, useRef } from 'react';
import { Stop } from '@/types';
import { formatCost } from '@/utils/currency';

interface Props {
  stops: Stop[];
  activeDay: number;
}


declare global {
  interface Window {
    L?: any;
    mapboxgl?: any;
  }
}

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '';

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

export default function MapView({ stops, activeDay }: Props) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<any>(null);
  const leafletMarkersRef = useRef<any[]>([]);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Load Leaflet (100% Free, No credit card, No API token required)
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(link);

    const script = document.createElement('script');
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    script.async = true;
    script.onload = () => {
      initLeafletMap();
    };
    document.head.appendChild(script);

    return () => {
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
      link.remove();
      script.remove();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const initLeafletMap = () => {
    if (!mapContainerRef.current || !window.L || leafletMapRef.current) return;

    const L = window.L;

    // Initialize map with dark background
    const map = L.map(mapContainerRef.current, {
      zoomControl: true,
      attributionControl: false,
    }).setView([20, 0], 2);

    // CartoDB Dark Matter tile layer — gorgeous nocturnal map, 100% free, no API key needed
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(map);

    leafletMapRef.current = map;
    updateLeafletMarkers();
  };

  const updateLeafletMarkers = () => {
    const map = leafletMapRef.current;
    const L = window.L;
    if (!map || !L) return;

    // Clear existing markers
    leafletMarkersRef.current.forEach(m => m.remove());
    leafletMarkersRef.current = [];

    if (!stops || stops.length === 0) return;

    const latLngs: [number, number][] = [];

    stops.forEach((stop, index) => {
      if (!stop.lat || !stop.lon) return;

      const lat = stop.lat;
      const lon = stop.lon;
      latLngs.push([lat, lon]);

      const color = stop.is_niche
        ? '#00DBE7'
        : (MARKER_COLORS[stop.category] ?? MARKER_COLORS.default);

      // Custom nocturnal pin HTML icon
      const customIcon = L.divIcon({
        className: 'custom-leaflet-marker',
        html: `
          <div style="
            width: 30px;
            height: 30px;
            border-radius: 50% 50% 50% 0;
            background: ${color};
            border: 2px solid rgba(255,255,255,0.4);
            transform: rotate(-45deg);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 14px rgba(0,0,0,0.5)${stop.is_niche ? `, 0 0 16px ${color}` : ''};
            cursor: pointer;
          ">
            <span style="
              transform: rotate(45deg);
              color: #040e1f;
              font-family: 'Sora', sans-serif;
              font-size: 11px;
              font-weight: 700;
              line-height: 1;
            ">${index + 1}</span>
          </div>
        `,
        iconSize: [30, 30],
        iconAnchor: [15, 30],
        popupAnchor: [0, -28],
      });

      const popupContent = `
        <div style="
          background: #0d192c;
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 10px;
          padding: 10px 12px;
          color: #d8e3fb;
          font-family: 'Outfit', sans-serif;
          min-width: 180px;
        ">
          ${stop.is_niche ? '<div style="color:#00DBE7;font-size:10px;font-weight:700;letter-spacing:0.08em;margin-bottom:4px">💎 HIDDEN GEM</div>' : ''}
          <div style="font-family:'Playfair Display',serif;font-size:15px;font-weight:600;color:#ffffff;margin-bottom:4px">${stop.name}</div>
          <div style="font-size:12px;color:#909096;text-transform:capitalize;margin-bottom:6px">${stop.category} · ${stop.duration_minutes} min</div>
          ${stop.estimated_cost_usd !== undefined ? `<div style="font-size:12px;color:#FFBF00;font-weight:600">${formatCost(stop.estimated_cost_usd, stop.address || stop.description || stop.name)}</div>` : ''}
        </div>

      `;

      const marker = L.marker([lat, lon], { icon: customIcon })
        .bindPopup(popupContent, {
          className: 'leaflet-dark-popup',
        })
        .addTo(map);

      leafletMarkersRef.current.push(marker);
    });

    // Auto-fit bounds
    if (latLngs.length === 1) {
      map.setView(latLngs[0], 14, { animate: true });
    } else if (latLngs.length > 1) {
      const bounds = L.latLngBounds(latLngs);
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15, animate: true });
    }
  };

  useEffect(() => {
    updateLeafletMarkers();
  }, [stops, activeDay]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div
      ref={mapContainerRef}
      style={{
        width: '100%',
        height: '100%',
        background: '#040e1f',
      }}
    />
  );
}
