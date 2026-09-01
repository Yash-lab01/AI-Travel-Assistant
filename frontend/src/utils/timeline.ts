/**
 * Timeline & Time-Slot Utility — Phase 7
 * Calculates concrete time blocks (e.g. 09:30 AM - 11:00 AM) and client-side transit times for sequential stops.
 */
import { Stop } from '@/types';

/**
 * Format total minutes from midnight into 12-hour AM/PM string (e.g. 570 -> "09:30 AM")
 */
export function minutesToTimeString(minutesFromMidnight: number): string {
  const normalized = Math.max(0, minutesFromMidnight % 1440);
  const hours24 = Math.floor(normalized / 60);
  const mins = normalized % 60;
  
  const period = hours24 >= 12 ? 'PM' : 'AM';
  const hours12 = hours24 % 12 === 0 ? 12 : hours24 % 12;
  const paddedMins = mins < 10 ? `0${mins}` : `${mins}`;
  
  return `${hours12}:${paddedMins} ${period}`;
}

/**
 * Compute concrete start and end time intervals for all stops in a day.
 * Default day starts at 09:00 AM (540 minutes).
 */
export function calculateDayTimeline(
  stops: Stop[],
  dayStartMinutes: number = 540 // 09:00 AM
): { stop: Stop; startTimeStr: string; endTimeStr: string; timeSlot: string; transitBefore: number }[] {
  if (!stops || stops.length === 0) return [];

  let currentMin = dayStartMinutes;
  const timeline = [];

  for (let i = 0; i < stops.length; i++) {
    const stop = stops[i];
    const transitBefore = i === 0 ? 0 : (stop.travel_time_from_prev_minutes || 15);
    
    // Add transit time
    currentMin += transitBefore;
    const startMin = currentMin;
    const duration = stop.duration_minutes || 60;
    const endMin = startMin + duration;
    currentMin = endMin;

    const startTimeStr = minutesToTimeString(startMin);
    const endTimeStr = minutesToTimeString(endMin);
    const timeSlot = `${startTimeStr} – ${endTimeStr}`;

    timeline.push({
      stop,
      startTimeStr,
      endTimeStr,
      timeSlot,
      transitBefore,
    });
  }

  return timeline;
}

/**
 * Haversine great-circle distance between two geographic coordinates in km.
 */
export function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371; // Earth radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Client-side optimistic recalculation of sequential transit times following a drag-and-drop reorder.
 */
export function recalculateSequentialTransit(stops: Stop[]): Stop[] {
  if (!stops || stops.length === 0) return [];

  return stops.map((stop, i) => {
    if (i === 0) {
      return { ...stop, travel_time_from_prev_minutes: 0 };
    }
    const prev = stops[i - 1];
    if (!prev || !prev.lat || !prev.lon || !stop.lat || !stop.lon) {
      return { ...stop, travel_time_from_prev_minutes: 15 };
    }

    const distKm = haversineKm(prev.lat, prev.lon, stop.lat, stop.lon);
    let minutes = 15;
    if (distKm <= 1.2) {
      minutes = Math.round((distKm / 4.5) * 60);
    } else {
      minutes = Math.round(4 + (distKm / 25.0) * 60);
    }

    const clamped = Math.max(5, Math.min(minutes, 50));
    return { ...stop, travel_time_from_prev_minutes: clamped };
  });
}
