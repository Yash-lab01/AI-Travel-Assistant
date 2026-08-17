'use client';

import { useEffect, useRef } from 'react';

interface City {
  name: string;
  x: number; // 0 to 1 normalized canvas coordinate
  y: number; // 0 to 1 normalized canvas coordinate
  isHub?: boolean;
}

interface FlightRoute {
  from: City;
  to: City;
  progress: number;
  speed: number;
  color: string;
  curvature: number; // curve offset
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  alpha: number;
  baseAlpha: number;
  color: string;
}

// Major global travel destinations mapped across a stylized equirectangular projection
const CITIES: City[] = [
  { name: 'Lisbon', x: 0.44, y: 0.38, isHub: true },
  { name: 'Tokyo', x: 0.88, y: 0.37, isHub: true },
  { name: 'Kyoto', x: 0.86, y: 0.39 },
  { name: 'Reykjavik', x: 0.41, y: 0.22, isHub: true },
  { name: 'Oaxaca', x: 0.22, y: 0.52 },
  { name: 'New York', x: 0.28, y: 0.36, isHub: true },
  { name: 'Paris', x: 0.48, y: 0.33, isHub: true },
  { name: 'Rome', x: 0.51, y: 0.38 },
  { name: 'Cairo', x: 0.55, y: 0.44 },
  { name: 'Dubai', x: 0.62, y: 0.45, isHub: true },
  { name: 'Bali', x: 0.82, y: 0.65 },
  { name: 'Sydney', x: 0.91, y: 0.76, isHub: true },
  { name: 'Cape Town', x: 0.52, y: 0.75 },
  { name: 'Rio de Janeiro', x: 0.34, y: 0.70 },
  { name: 'Bangkok', x: 0.77, y: 0.49 },
  { name: 'Honolulu', x: 0.08, y: 0.47 },
  { name: 'Vancouver', x: 0.19, y: 0.31 },
  { name: 'Lima', x: 0.26, y: 0.63 },
  { name: 'London', x: 0.46, y: 0.31, isHub: true },
  { name: 'Singapore', x: 0.78, y: 0.57, isHub: true },
];

const ROUTE_PAIRS: [number, number][] = [
  [0, 6],   // Lisbon -> Paris
  [6, 1],   // Paris -> Tokyo
  [0, 5],   // Lisbon -> New York
  [5, 4],   // New York -> Oaxaca
  [5, 3],   // New York -> Reykjavik
  [3, 18],  // Reykjavik -> London
  [18, 9],  // London -> Dubai
  [9, 14],  // Dubai -> Bangkok
  [14, 1],  // Bangkok -> Tokyo
  [1, 2],   // Tokyo -> Kyoto
  [1, 11],  // Tokyo -> Sydney
  [9, 10],  // Dubai -> Bali
  [10, 11], // Bali -> Sydney
  [0, 13],  // Lisbon -> Rio
  [13, 12], // Rio -> Cape Town
  [12, 9],  // Cape Town -> Dubai
  [16, 5],  // Vancouver -> New York
  [5, 15],  // New York -> Honolulu
  [15, 1],  // Honolulu -> Tokyo
  [6, 7],   // Paris -> Rome
  [7, 8],   // Rome -> Cairo
];

export default function TravelLiveWallpaper() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    let mouseX = width * 0.5;
    let mouseY = height * 0.4;
    let targetMouseX = mouseX;
    let targetMouseY = mouseY;

    // Handle high DPI
    const handleResize = () => {
      if (!canvas) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = canvas.width = window.innerWidth * dpr;
      height = canvas.height = window.innerHeight * dpr;
      ctx.scale(dpr, dpr);
      width = window.innerWidth;
      height = window.innerHeight;
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    const handleMouseMove = (e: MouseEvent) => {
      targetMouseX = e.clientX;
      targetMouseY = e.clientY;
    };
    window.addEventListener('mousemove', handleMouseMove);

    // Initialize flight routes
    const routes: FlightRoute[] = ROUTE_PAIRS.map(([fromIdx, toIdx], index) => {
      const isAmber = index % 2 === 0;
      return {
        from: CITIES[fromIdx],
        to: CITIES[toIdx],
        progress: Math.random(),
        speed: 0.0012 + Math.random() * 0.0016,
        color: isAmber ? '#FFBF00' : '#00DBE7',
        curvature: (index % 3 - 1) * 0.18, // dynamic curve offset
      };
    });

    // Initialize floating ambient stars / particles
    const particleCount = 75;
    const particles: Particle[] = Array.from({ length: particleCount }, () => {
      const isAmber = Math.random() > 0.65;
      const baseAlpha = 0.15 + Math.random() * 0.4;
      return {
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.25,
        vy: (Math.random() - 0.5) * 0.25,
        size: 1 + Math.random() * 2,
        alpha: baseAlpha,
        baseAlpha,
        color: isAmber ? '255, 191, 0' : '0, 219, 231',
      };
    });

    // Radar scan ring state
    let radarRadius = 0;
    let radarCityIdx = 0;

    let time = 0;

    const render = () => {
      time += 0.016;

      // Smooth mouse follow
      mouseX += (targetMouseX - mouseX) * 0.04;
      mouseY += (targetMouseY - mouseY) * 0.04;

      ctx.clearRect(0, 0, width, height);

      // ── 1. Dynamic Deep Atmosphere & Aurora Glows ────────────────
      // Base dark radial gradient
      const bgGrad = ctx.createLinearGradient(0, 0, 0, height);
      bgGrad.addColorStop(0, '#040e1f');
      bgGrad.addColorStop(0.4, '#061226');
      bgGrad.addColorStop(0.8, '#08172e');
      bgGrad.addColorStop(1, '#050c1b');
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      // Aurora oceanic glow in top-right (Tokyo / Pacific corridor)
      const auroraTeal = ctx.createRadialGradient(
        width * 0.75 + Math.sin(time * 0.5) * 60,
        height * 0.35 + Math.cos(time * 0.4) * 40,
        20,
        width * 0.75,
        height * 0.35,
        width * 0.55
      );
      auroraTeal.addColorStop(0, 'rgba(0, 219, 231, 0.08)');
      auroraTeal.addColorStop(0.5, 'rgba(14, 165, 233, 0.03)');
      auroraTeal.addColorStop(1, 'transparent');
      ctx.fillStyle = auroraTeal;
      ctx.fillRect(0, 0, width, height);

      // Aurora warm golden amber glow in left (Atlantic / Lisbon corridor)
      const auroraAmber = ctx.createRadialGradient(
        width * 0.3 + Math.cos(time * 0.6) * 50,
        height * 0.45 + Math.sin(time * 0.5) * 40,
        20,
        width * 0.3,
        height * 0.45,
        width * 0.5
      );
      auroraAmber.addColorStop(0, 'rgba(255, 191, 0, 0.065)');
      auroraAmber.addColorStop(0.6, 'rgba(232, 168, 56, 0.02)');
      auroraAmber.addColorStop(1, 'transparent');
      ctx.fillStyle = auroraAmber;
      ctx.fillRect(0, 0, width, height);

      // Interactive mouse cursor spotlight glow
      const mouseGlow = ctx.createRadialGradient(mouseX, mouseY, 0, mouseX, mouseY, 320);
      mouseGlow.addColorStop(0, 'rgba(0, 219, 231, 0.06)');
      mouseGlow.addColorStop(0.5, 'rgba(255, 191, 0, 0.03)');
      mouseGlow.addColorStop(1, 'transparent');
      ctx.fillStyle = mouseGlow;
      ctx.fillRect(0, 0, width, height);

      // ── 2. Subtle Global Navigation Grid (Latitude/Longitude curves) ──
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.025)';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 12]);

      // Latitudinal curved lines
      for (let lat = 0.2; lat <= 0.8; lat += 0.15) {
        ctx.beginPath();
        ctx.moveTo(0, height * lat);
        ctx.bezierCurveTo(
          width * 0.33,
          height * (lat - 0.03),
          width * 0.66,
          height * (lat + 0.03),
          width,
          height * lat
        );
        ctx.stroke();
      }

      // Longitudinal lines
      for (let lon = 0.15; lon <= 0.9; lon += 0.18) {
        ctx.beginPath();
        ctx.moveTo(width * lon, 0);
        ctx.quadraticCurveTo(width * (lon + 0.04), height * 0.5, width * lon, height);
        ctx.stroke();
      }
      ctx.setLineDash([]); // Reset dash

      // ── 3. Drifting Ambient Stars & Flight Particles ─────────────
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        // Subtle twinkling
        const twinkle = Math.sin(time * 3 + p.x * 0.01) * 0.2;
        const currentAlpha = Math.max(0.05, Math.min(0.8, p.baseAlpha + twinkle));

        ctx.fillStyle = `rgba(${p.color}, ${currentAlpha})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      });

      // ── 4. Radar Pulse Expanding from Selected Hub ──────────────
      radarRadius += 1.2;
      const hub = CITIES[radarCityIdx];
      const hubX = hub.x * width;
      const hubY = hub.y * height;
      const maxRadius = 180;

      if (radarRadius > maxRadius) {
        radarRadius = 0;
        radarCityIdx = (radarCityIdx + 1) % CITIES.length;
      }

      const radarAlpha = Math.max(0, (1 - radarRadius / maxRadius) * 0.25);
      ctx.strokeStyle = `rgba(0, 219, 231, ${radarAlpha})`;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(hubX, hubY, radarRadius, 0, Math.PI * 2);
      ctx.stroke();

      // ── 5. Flight Routes (Great Circle Arcs) ────────────────────
      routes.forEach((route) => {
        const x1 = route.from.x * width;
        const y1 = route.from.y * height;
        const x2 = route.to.x * width;
        const y2 = route.to.y * height;

        // Midpoint and perpendicular curve control point
        const midX = (x1 + x2) / 2;
        const midY = (y1 + y2) / 2;
        const dx = x2 - x1;
        const dy = y2 - y1;
        const dist = Math.sqrt(dx * dx + dy * dy);

        // Control point curved upwards / offset
        const normalX = -dy / dist;
        const normalY = dx / dist;
        const curveOffset = dist * (route.curvature || -0.22);
        const ctrlX = midX + normalX * curveOffset;
        const ctrlY = midY + normalY * curveOffset;

        // Draw static faint flight path
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.quadraticCurveTo(ctrlX, ctrlY, x2, y2);
        ctx.strokeStyle =
          route.color === '#FFBF00'
            ? 'rgba(255, 191, 0, 0.09)'
            : 'rgba(0, 219, 231, 0.09)';
        ctx.lineWidth = 1.2;
        ctx.setLineDash([3, 6]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Advance flight packet
        route.progress += route.speed;
        if (route.progress > 1) {
          route.progress = 0;
        }

        const t = route.progress;
        // Quadratic Bezier interpolation: B(t) = (1-t)^2 P0 + 2(1-t)t P1 + t^2 P2
        const currentX = (1 - t) * (1 - t) * x1 + 2 * (1 - t) * t * ctrlX + t * t * x2;
        const currentY = (1 - t) * (1 - t) * y1 + 2 * (1 - t) * t * ctrlY + t * t * y2;

        // Trail positions (5 steps behind)
        for (let trail = 5; trail >= 1; trail--) {
          const tTrail = Math.max(0, t - trail * 0.014);
          const trX = (1 - tTrail) * (1 - tTrail) * x1 + 2 * (1 - tTrail) * tTrail * ctrlX + tTrail * tTrail * x2;
          const trY = (1 - tTrail) * (1 - tTrail) * y1 + 2 * (1 - tTrail) * tTrail * ctrlY + tTrail * tTrail * y2;
          const trailAlpha = (1 - trail / 6) * 0.35;

          ctx.fillStyle =
            route.color === '#FFBF00'
              ? `rgba(255, 191, 0, ${trailAlpha})`
              : `rgba(0, 219, 231, ${trailAlpha})`;
          ctx.beginPath();
          ctx.arc(trX, trY, 1.4, 0, Math.PI * 2);
          ctx.fill();
        }

        // Flight Packet Head (Glowing Airplane / Comet Head)
        const isAmber = route.color === '#FFBF00';
        ctx.fillStyle = isAmber ? '#FFF3B0' : '#E0F7FA';
        ctx.shadowColor = route.color;
        ctx.shadowBlur = 12;
        ctx.beginPath();
        ctx.arc(currentX, currentY, 2.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0; // Reset shadow blur
      });

      // ── 6. World Destinations (Waypoints & Beacon Rings) ────────
      CITIES.forEach((city) => {
        const cx = city.x * width;
        const cy = city.y * height;

        // Outer pulse ring
        const pulse = (Math.sin(time * 2.5 + city.x * 10) + 1) * 0.5;
        const isHub = city.isHub;

        // Hub aura
        if (isHub) {
          ctx.fillStyle = 'rgba(255, 191, 0, 0.08)';
          ctx.beginPath();
          ctx.arc(cx, cy, 14 + pulse * 6, 0, Math.PI * 2);
          ctx.fill();

          ctx.strokeStyle = 'rgba(255, 191, 0, 0.3)';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.arc(cx, cy, 8 + pulse * 4, 0, Math.PI * 2);
          ctx.stroke();
        }

        // Center dot
        ctx.fillStyle = isHub ? '#FFBF00' : '#00DBE7';
        ctx.shadowColor = isHub ? '#FFBF00' : '#00DBE7';
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.arc(cx, cy, isHub ? 3.5 : 2.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        // City labels (subtle typography)
        if (isHub || width > 900) {
          ctx.font = '500 10px Sora, sans-serif';
          ctx.fillStyle = 'rgba(216, 227, 251, 0.45)';
          ctx.fillText(city.name, cx + 8, cy + 3);
        }
      });

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 0,
        pointerEvents: 'none',
        display: 'block',
      }}
      aria-hidden="true"
    />
  );
}
