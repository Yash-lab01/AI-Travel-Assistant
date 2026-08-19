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
    if (typeof window === 'undefined') return;

    // Load Leaflet CSS if not already present
    if (!document.getElementById('leaflet-css')) {
      const link = document.createElement('link');
      link.id = 'leaflet-css';
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      document.head.appendChild(link);
    }

    // Load Leaflet JS if not already loaded
    if (!window.L) {
      const script = document.createElement('script');
      script.id = 'leaflet-js';
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.onload = () => initLeafletMap();
      document.head.appendChild(script);
    } else {
      initLeafletMap();
    }

    return () => {
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const initLeafletMap = () => {
    if (!mapContainerRef.current || !window.L || leafletMapRef.current) return;

    const L = window.L;

    // Initialize map with dark background
    const map = L.map(mapContainerRef.current, {
      zoomControl: true,
      attributionControl: false,
    }).setView([18.5204, 73.8567], 12);

    // CartoDB Dark Matter tile layer — gorgeous nocturnal map, 100% free, zero token requirement
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
    leafletMarkersRef.current.forEach(m => {
      try { m.remove(); } catch {}
    });
    leafletMarkersRef.current = [];

    if (!stops || stops.length === 0) return;

    const latLngs: [number, number][] = [];

    stops.forEach((stop, index) => {
      if (!stop || typeof stop.lat !== 'number' || typeof stop.lon !== 'number' || isNaN(stop.lat) || isNaN(stop.lon)) {
        return;
      }

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

      const photoImg = stop.photo_urls && stop.photo_urls.length > 0
        ? `<div style="width:100%;height:100px;border-radius:6px;overflow:hidden;margin-bottom:8px;background:#15233a;">
             <img src="${stop.photo_urls[0]}" alt="${stop.name || 'Stop'}" style="width:100%;height:100%;object-fit:cover;display:block;" onerror="this.parentElement.style.display='none'" />
           </div>`
        : '';

      const popupContent = `
        <div style="
          background: #0d192c;
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 10px;
          padding: 10px 12px;
          color: #d8e3fb;
          font-family: 'Outfit', sans-serif;
          min-width: 200px;
          max-width: 240px;
        ">
          ${photoImg}
          ${stop.is_niche ? '<div style="color:#00DBE7;font-size:10px;font-weight:700;letter-spacing:0.08em;margin-bottom:4px">💎 HIDDEN GEM</div>' : ''}
          <div style="font-family:'Playfair Display',serif;font-size:15px;font-weight:600;color:#ffffff;margin-bottom:4px">${stop.name || 'Stop'}</div>
          <div style="font-size:12px;color:#909096;text-transform:capitalize;margin-bottom:6px">${stop.category || 'Attraction'} · ${stop.duration_minutes || 60} min</div>
          ${stop.estimated_cost_usd !== undefined ? `<div style="font-size:12px;color:#FFBF00;font-weight:600">${formatCost(stop.estimated_cost_usd, stop.address || stop.description || stop.name)}</div>` : ''}
        </div>
      `;

      try {
        const marker = L.marker([lat, lon], { icon: customIcon })
          .bindPopup(popupContent, {
            className: 'leaflet-dark-popup',
          })
          .addTo(map);

        leafletMarkersRef.current.push(marker);
      } catch (err) {
        console.warn('Marker create error:', err);
      }
    });

    // Auto-fit bounds safely with container layout validation
    if (latLngs.length === 1) {
      try {
        map.setView(latLngs[0], 14, { animate: true });
      } catch {}
    } else if (latLngs.length > 1) {
      setTimeout(() => {
        try {
          if (!leafletMapRef.current || !mapContainerRef.current) return;
          leafletMapRef.current.invalidateSize();
          const bounds = L.latLngBounds(latLngs);
          if (bounds.isValid()) {
            const ne = bounds.getNorthEast();
            const sw = bounds.getSouthWest();
            if (ne && sw && ne.lat === sw.lat && ne.lng === sw.lng) {
              leafletMapRef.current.setView([ne.lat, ne.lng], 14, { animate: true });
            } else {
              leafletMapRef.current.fitBounds(bounds, { padding: [40, 40], maxZoom: 15, animate: true });
            }
          }
        } catch {
          // Gracefully suppress expected Leaflet initial render layout warnings
        }
      }, 50);
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
        minHeight: 480,
        background: '#040e1f',
        position: 'relative',
        zIndex: 1,
      }}
    />
  );
}
