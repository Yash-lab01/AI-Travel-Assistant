"""
PDF Export Generator for WanderAI Itineraries — Phase 6
Generates high-fidelity, printable PDF travel brochures using Playwright headless Chromium.

Features:
- Editorial layout with Google Fonts (Outfit & Playfair Display)
- Destination header banner, trip badges (duration, style, pace, cost)
- Day-by-day itineraries with weather forecasts, day cost estimates, and themes
- Numbered stop cards with real photography, category badges, durations, and atmospheric narrations
- Sequential transit connectors between stops
- Cost summary breakdown and WanderAI branding
"""
from __future__ import annotations
import os
import asyncio
from datetime import datetime, timezone
from typing import Optional
from playwright.async_api import async_playwright

from app.models.schemas import Itinerary, Stop, DayPlan


def _format_currency(usd_amount: float, destination: str = "") -> str:
    """Format USD and approximate local currency for India / Europe."""
    if usd_amount is None or usd_amount <= 0:
        return "Free"
    
    dest_lower = destination.lower()
    if any(x in dest_lower for x in ["india", "goa", "mumbai", "pune", "delhi", "jaipur", "kerala", "rajasthan", "bengaluru"]):
        inr = int(usd_amount * 85)
        return f"₹{inr:,} (~${usd_amount:.0f})"
    elif any(x in dest_lower for x in ["paris", "rome", "lisbon", "france", "italy", "portugal", "spain", "berlin", "amsterdam"]):
        eur = round(usd_amount * 0.92, 1)
        return f"€{eur:.0f} (${usd_amount:.0f})"
    return f"${usd_amount:.0f} USD"


def generate_itinerary_html(itinerary: Itinerary) -> str:
    """Render the full HTML document for PDF conversion."""
    dest = itinerary.trip_request.destination if itinerary.trip_request else "Destination"
    num_days = len(itinerary.days)
    travel_style = itinerary.trip_request.travel_style if itinerary.trip_request else "balanced"
    pace = itinerary.trip_request.pace if itinerary.trip_request else "moderate"
    total_cost = itinerary.total_cost_estimate_usd or 0.0
    formatted_total_cost = _format_currency(total_cost, dest)
    generated_date = datetime.now(timezone.utc).strftime("%B %d, %Y")

    cover_image = getattr(itinerary, 'cover_image_url', None) or "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1200&q=80"

    days_html = []
    for day in itinerary.days:
        day_cost_str = _format_currency(day.day_cost_estimate_usd, dest)
        weather_html = f'<div class="weather-pill">🌤️ {day.weather_note}</div>' if day.weather_note else ''
        
        stops_html = []
        for idx, stop in enumerate(day.stops):
            stop_cost_str = _format_currency(stop.estimated_cost_usd, dest)
            is_gem_badge = '<span class="gem-badge">💎 HIDDEN GEM</span>' if stop.is_niche else ''
            
            photo_html = ''
            if stop.photo_urls and len(stop.photo_urls) > 0:
                photo_html = f'''
                <div class="stop-image-wrap">
                    <img src="{stop.photo_urls[0]}" class="stop-img" alt="{stop.name}" />
                </div>
                '''

            transit_connector = ''
            if idx > 0 and getattr(stop, 'travel_time_from_prev_minutes', None) is not None:
                mins = stop.travel_time_from_prev_minutes
                mode = "walk" if mins <= 12 else "transit"
                transit_connector = f'''
                <div class="transit-connector">
                    <span class="transit-icon">➔</span>
                    <span class="transit-text">{mins} min {mode} from previous stop</span>
                </div>
                '''

            narration_html = f'<p class="stop-narration">"{stop.narration}"</p>' if stop.narration else ''

            stops_html.append(f'''
            <div class="stop-card">
                <div class="stop-left">
                    <div class="stop-num">{idx + 1}</div>
                    {photo_html}
                </div>
                <div class="stop-body">
                    <div class="stop-header">
                        <div class="stop-meta-row">
                            <span class="category-tag">{stop.category.upper() if stop.category else 'ATTRACTION'}</span>
                            {is_gem_badge}
                            <span class="duration-tag">⏱️ {stop.duration_minutes or 60} mins</span>
                            <span class="cost-tag">💳 {stop_cost_str}</span>
                        </div>
                        <h4 class="stop-name">{stop.name}</h4>
                    </div>
                    {narration_html}
                    <p class="stop-desc">{stop.description or ''}</p>
                </div>
            </div>
            {transit_connector}
            ''')

        days_html.append(f'''
        <div class="day-section">
            <div class="day-header">
                <div class="day-badge">DAY {day.day_number}</div>
                <div class="day-title-wrap">
                    <h3 class="day-theme">{day.theme}</h3>
                    <div class="day-meta">
                        {weather_html}
                        <div class="day-cost">Est. Day Cost: <strong>{day_cost_str}</strong></div>
                    </div>
                </div>
            </div>
            <div class="stops-container">
                {''.join(stops_html)}
            </div>
        </div>
        ''')

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>WanderAI Travel Itinerary — {dest}</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700;800&family=Sora:wght@600;700&display=swap');

    @page {{
        size: A4;
        margin: 12mm 14mm;
    }}

    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}

    body {{
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #0d192c;
        background: #ffffff;
        line-height: 1.45;
        font-size: 11pt;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}

    /* Header Banner */
    .hero-banner {{
        position: relative;
        background: linear-gradient(135deg, #040e1f 0%, #0d1e38 100%);
        border-radius: 12px;
        color: #ffffff;
        padding: 24px 28px;
        margin-bottom: 24px;
        overflow: hidden;
        border: 1px solid #1a2f52;
    }}

    .hero-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        border-bottom: 1px solid rgba(255,255,255,0.15);
        padding-bottom: 12px;
    }}

    .brand-logo {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 20pt;
        font-weight: 800;
        color: #00DBE7;
        letter-spacing: -0.02em;
    }}

    .brand-logo span {{
        color: #ffffff;
    }}

    .export-date {{
        font-size: 9pt;
        color: #8da2c0;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}

    .hero-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 26pt;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.15;
        margin-bottom: 12px;
    }}

    .hero-badges {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }}

    .badge {{
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 8.5pt;
        color: #d8e3fb;
        font-weight: 500;
        text-transform: capitalize;
    }}

    .badge.highlight {{
        background: rgba(0, 219, 231, 0.15);
        border-color: #00DBE7;
        color: #00DBE7;
        font-weight: 600;
    }}

    .badge.gold {{
        background: rgba(232, 168, 56, 0.15);
        border-color: #E8A838;
        color: #E8A838;
        font-weight: 600;
    }}

    /* Day Section */
    .day-section {{
        margin-bottom: 24px;
        page-break-inside: avoid;
    }}

    .day-header {{
        display: flex;
        align-items: center;
        gap: 14px;
        background: #f1f5f9;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid #00DBE7;
        margin-bottom: 14px;
    }}

    .day-badge {{
        font-family: 'Sora', sans-serif;
        background: #040e1f;
        color: #00DBE7;
        font-weight: 700;
        font-size: 10pt;
        padding: 4px 10px;
        border-radius: 6px;
        letter-spacing: 0.05em;
    }}

    .day-title-wrap {{
        flex: 1;
    }}

    .day-theme {{
        font-family: 'Playfair Display', serif;
        font-size: 14pt;
        font-weight: 700;
        color: #040e1f;
        margin-bottom: 2px;
    }}

    .day-meta {{
        display: flex;
        gap: 14px;
        font-size: 8.5pt;
        color: #64748b;
        align-items: center;
    }}

    .weather-pill {{
        color: #0284c7;
        font-weight: 500;
    }}

    .day-cost strong {{
        color: #0f172a;
    }}

    /* Stop Card */
    .stop-card {{
        display: flex;
        gap: 14px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 8px;
        page-break-inside: avoid;
    }}

    .stop-left {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        width: 80px;
        flex-shrink: 0;
    }}

    .stop-num {{
        width: 24px;
        height: 24px;
        background: #040e1f;
        color: #ffffff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 9pt;
        font-weight: 700;
        font-family: 'Sora', sans-serif;
    }}

    .stop-image-wrap {{
        width: 80px;
        height: 60px;
        border-radius: 6px;
        overflow: hidden;
        background: #e2e8f0;
    }}

    .stop-img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }}

    .stop-body {{
        flex: 1;
    }}

    .stop-header {{
        margin-bottom: 4px;
    }}

    .stop-meta-row {{
        display: flex;
        gap: 6px;
        align-items: center;
        margin-bottom: 3px;
        flex-wrap: wrap;
    }}

    .category-tag {{
        font-size: 7pt;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        background: #f1f5f9;
        color: #475569;
        letter-spacing: 0.04em;
    }}

    .gem-badge {{
        font-size: 7pt;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        background: #e0f2fe;
        color: #0369a1;
        letter-spacing: 0.04em;
    }}

    .duration-tag, .cost-tag {{
        font-size: 7.5pt;
        color: #64748b;
        font-weight: 500;
    }}

    .stop-name {{
        font-family: 'Playfair Display', serif;
        font-size: 12.5pt;
        font-weight: 700;
        color: #0f172a;
    }}

    .stop-narration {{
        font-style: italic;
        color: #334155;
        font-size: 9pt;
        line-height: 1.35;
        margin-bottom: 4px;
        background: #f8fafc;
        padding: 4px 8px;
        border-left: 2px solid #00DBE7;
        border-radius: 2px;
    }}

    .stop-desc {{
        font-size: 8.5pt;
        color: #64748b;
        line-height: 1.3;
    }}

    /* Transit Connector */
    .transit-connector {{
        display: flex;
        align-items: center;
        gap: 6px;
        padding-left: 28px;
        margin: 4px 0 8px;
        color: #64748b;
        font-size: 7.5pt;
        font-weight: 500;
    }}

    .transit-icon {{
        font-size: 9pt;
    }}

    /* Footer & Cost Summary */
    .trip-summary-box {{
        background: #040e1f;
        color: #ffffff;
        border-radius: 10px;
        padding: 16px 20px;
        margin-top: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        page-break-inside: avoid;
    }}

    .summary-left h4 {{
        font-family: 'Playfair Display', serif;
        font-size: 14pt;
        color: #ffffff;
        margin-bottom: 2px;
    }}

    .summary-left p {{
        font-size: 8.5pt;
        color: #94a3b8;
    }}

    .summary-right {{
        text-align: right;
    }}

    .total-cost-val {{
        font-family: 'Sora', sans-serif;
        font-size: 16pt;
        font-weight: 700;
        color: #E8A838;
    }}

    .footer-note {{
        text-align: center;
        margin-top: 18px;
        font-size: 7.5pt;
        color: #94a3b8;
    }}
</style>
</head>
<body>

<div class="hero-banner">
    <div class="hero-top">
        <div class="brand-logo">Wander<span>AI</span></div>
        <div class="export-date">Generated: {generated_date}</div>
    </div>
    <h1 class="hero-title">{num_days}-Day {dest} Itinerary</h1>
    <div class="hero-badges">
        <span class="badge highlight">📍 {dest}</span>
        <span class="badge">📅 {num_days} Days</span>
        <span class="badge">🎒 {travel_style} Style</span>
        <span class="badge">⚡ {pace} Pace</span>
        <span class="badge gold">💰 Total: {formatted_total_cost}</span>
    </div>
</div>

{''.join(days_html)}

<div class="trip-summary-box">
    <div class="summary-left">
        <h4>WanderAI Travel Plan Overview</h4>
        <p>Curated with local hidden gems, optimal transit times, and weather-aware planning.</p>
    </div>
    <div class="summary-right">
        <div style="font-size: 8pt; color: #94a3b8; text-transform: uppercase;">Estimated Total Cost</div>
        <div class="total-cost-val">{formatted_total_cost}</div>
    </div>
</div>

<div class="footer-note">
    Created with WanderAI · AI-Powered Multi-Agent Travel Planner · https://wanderai.app
</div>

</body>
</html>
'''
    return html_content


async def generate_itinerary_pdf(itinerary: Itinerary) -> bytes:
    """
    Render an Itinerary into high-quality A4 PDF bytes using Playwright Chromium.
    Falls back to a clean printable HTML document encoded in bytes if browser fails.
    """
    html = generate_itinerary_html(itinerary)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            # Set HTML content and wait for images/fonts
            await page.set_content(html, wait_until="networkidle", timeout=12000)
            pdf_bytes = await page.pdf(
                format="A4",
                print_background=True,
                margin={
                    "top": "10mm",
                    "bottom": "10mm",
                    "left": "10mm",
                    "right": "10mm",
                },
            )
            await browser.close()
            if pdf_bytes and len(pdf_bytes) > 1000:
                return pdf_bytes
    except Exception as e:
        print(f"[pdf_generator] Playwright Chromium PDF generation note: {e}")

    # Fallback: return formatted HTML bytes (clients can open and print)
    return html.encode("utf-8")
