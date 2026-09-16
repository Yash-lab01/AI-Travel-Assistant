'use client';

import { useState, useEffect } from 'react';
import ChatPanel from '@/components/ChatPanel';
import ItineraryView from '@/components/ItineraryView';
import TravelLiveWallpaper from '@/components/TravelLiveWallpaper';
import TripHistoryPanel from '@/components/TripHistoryPanel';
import ErrorBoundary from '@/components/ErrorBoundary';
import { ToastProvider } from '@/components/Toast';
import { applyDestinationTheme } from '@/utils/destinationTheme';
import { AgentEvent, Itinerary, StopEditRequest, TripHistoryRecord } from '@/types';

const HERO_PROMPT_CARDS = [
  {
    flag: '🌴',
    destination: 'Goa, India',
    prompt: '3 days in Goa, beaches, Portuguese heritage & cafes',
    tag: 'Coastal & Heritage',
    image: 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&auto=format&fit=crop&q=80',
  },
  {
    flag: '👑',
    destination: 'Rajasthan, India',
    prompt: '4 days in Rajasthan, Jaipur royal forts, stepwells & desert street food',
    tag: 'Heritage & Royal Forts',
    image: 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800&auto=format&fit=crop&q=80',
  },
  {
    flag: '🇵🇹',
    destination: 'Lisbon, Portugal',
    prompt: '3 days in Lisbon, iconic landmarks, hidden miradouros & authentic Fado',
    tag: 'Culture & Coast',
    image: 'https://images.unsplash.com/photo-1588668214407-6ea9a6d8c272?w=800&auto=format&fit=crop&q=80',
  },
  {
    flag: '🇯🇵',
    destination: 'Kyoto, Japan',
    prompt: '4 days in Kyoto, iconic zen temples, bamboo groves & local ramen',
    tag: 'Zen & Gastronomy',
    image: 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800&auto=format&fit=crop&q=80',
  },
];

export default function Home() {
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [agentEvents, setAgentEvents] = useState<AgentEvent[]>([]);
  const [externalPrompt, setExternalPrompt] = useState<string | null>(null);
  const [externalEditInstruction, setExternalEditInstruction] = useState<string | null>(null);
  const [externalAction, setExternalAction] = useState<StopEditRequest | null>(null);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [savedHistoryCount, setSavedHistoryCount] = useState(0);
  const [activeMobileTab, setActiveMobileTab] = useState<'studio' | 'itinerary' | 'history' | 'about'>('studio');

  const updateHistoryCount = () => {
    try {
      const stored = localStorage.getItem('wanderai_trip_history');
      if (stored) {
        const parsed = JSON.parse(stored);
        setSavedHistoryCount(Array.isArray(parsed) ? parsed.length : 0);
      } else {
        setSavedHistoryCount(0);
      }
    } catch {
      setSavedHistoryCount(0);
    }
  };

  // Ensure page always starts at top on initial load
  useEffect(() => {
    if (typeof window !== 'undefined') {
      if ('scrollRestoration' in window.history) {
        window.history.scrollRestoration = 'manual';
      }
      window.scrollTo(0, 0);
      updateHistoryCount();
    }
  }, []);

  // Auto-scroll to itinerary visualizer when it becomes available
  useEffect(() => {
    if (itinerary) {
      applyDestinationTheme(itinerary.trip_request?.destination);
      setTimeout(() => {
        const itineraryEl = document.getElementById('itinerary-visualizer');
        if (itineraryEl) {
          itineraryEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 300);
    }
  }, [itinerary]);

  const handleItineraryReceived = (newItinerary: Itinerary) => {
    setItinerary(newItinerary);
    applyDestinationTheme(newItinerary.trip_request?.destination);

    // Auto-save to localStorage (up to 10 trips)
    try {
      const stored = localStorage.getItem('wanderai_trip_history');
      let currentTrips: TripHistoryRecord[] = stored ? JSON.parse(stored) : [];
      currentTrips = currentTrips.filter((t) => t.id !== newItinerary.id);

      const record: TripHistoryRecord = {
        id: newItinerary.id,
        destination: newItinerary.trip_request?.destination || 'Destination',
        num_days: newItinerary.days?.length || 1,
        total_cost_usd: newItinerary.total_cost_estimate_usd,
        cover_image_url: newItinerary.cover_image_url || newItinerary.days?.[0]?.cover_image_url,
        created_at: new Date().toISOString(),
        itinerary: newItinerary,
      };

      currentTrips.unshift(record);
      if (currentTrips.length > 10) currentTrips = currentTrips.slice(0, 10);
      localStorage.setItem('wanderai_trip_history', JSON.stringify(currentTrips));
      setSavedHistoryCount(currentTrips.length);
    } catch (e) {
      console.warn('Failed to auto-save to localStorage', e);
    }

    // Sync to backend SQLite /history
    fetch('http://localhost:8000/history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newItinerary),
    }).catch((err) => console.warn('Failed to sync to backend /history', err));
  };

  const handleSelectSavedTrip = (savedItinerary: Itinerary) => {
    setItinerary(savedItinerary);
    setIsStreaming(false);
    applyDestinationTheme(savedItinerary.trip_request?.destination);
    setTimeout(() => {
      const visualizer = document.getElementById('itinerary-visualizer');
      if (visualizer) {
        visualizer.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } else {
        scrollToSection('planner-studio');
      }
    }, 150);
  };

  const handleHeroPromptSelect = (promptText: string) => {
    setExternalPrompt(promptText);
    const studioElement = document.getElementById('planner-studio');
    if (studioElement) {
      studioElement.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const scrollToSection = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <ToastProvider>
      {/* Travel-Themed Live Wallpaper Canvas & Aurora Glow */}
      <TravelLiveWallpaper />

      {/* Slide-over Trip History Drawer */}
      <TripHistoryPanel
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        onSelectTrip={handleSelectSavedTrip}
        currentItineraryId={itinerary?.id}
        onHistoryUpdated={updateHistoryCount}
      />

      <div className="main-wrapper">
        {/* Navigation Bar */}
        <header className="site-header">
          <div className="header-left">
            <div className="logo-group" onClick={() => scrollToSection('intro')}>
              <div className="logo-mark">🧭</div>
              <span className="logo-text">WanderAI</span>
            </div>
            <div className="badge">
              <span className="live-dot" />
              <span>Multi-Agent Swarm</span>
            </div>
          </div>

          <nav className="nav-links">
            <a className="nav-link" onClick={() => scrollToSection('intro')}>Home</a>
            <a className="nav-link" onClick={() => scrollToSection('overview')}>Overview</a>
            <a className="nav-link" onClick={() => scrollToSection('how-it-works')}>Architecture</a>
            <a className="nav-link" onClick={() => scrollToSection('planner-studio')}>Interactive Studio</a>
          </nav>

          <div className="header-right">
            {/* History Trigger Button */}
            <button
              type="button"
              className="btn-history-toggle"
              onClick={() => setIsHistoryOpen(true)}
              title="View saved trip history"
            >
              <span>🗂️ History</span>
              {savedHistoryCount > 0 && (
                <span className="history-badge-count">{savedHistoryCount}</span>
              )}
            </button>

            {itinerary && (
              <button
                onClick={() => window.open(`http://localhost:8000/export/pdf/${itinerary.id}`, '_blank')}
                style={{
                  background: 'transparent',
                  border: '1px solid var(--glass-border-amber)',
                  borderRadius: 'var(--radius-full)',
                  color: 'var(--amber)',
                  padding: '6px 14px',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontFamily: 'var(--font-label)',
                  transition: 'all 200ms',
                }}
              >
                📄 Export PDF
              </button>
            )}
            <button
              className="btn-primary-sm"
              onClick={() => scrollToSection('planner-studio')}
            >
              <span>Launch Studio ↓</span>
            </button>
          </div>
        </header>

        {/* 100vh Minimalist Brand Showcase Intro Screen */}
        <section id="intro" className="intro-hero-screen">
          <div className="intro-badge-pill">
            <span className="live-dot" />
            <span>AUTONOMOUS MULTI-AGENT TRAVEL STUDIO</span>
          </div>

          <div className="intro-brand-container">
            <div className="intro-emblem-glow">🧭</div>
            <h1 className="intro-brand-title gradient-text-hero">WanderAI</h1>
          </div>

          <p className="intro-tagline">
            Type a destination. A swarm of 6 specialized AI agents builds your full day-by-day itinerary —
            landmarks, hidden gems, geo-clustered stops, weather, costs, and a packing list.
          </p>

          <div className="intro-scroll-wrapper">
            <button
              className="intro-scroll-btn"
              onClick={() => scrollToSection('overview')}
              aria-label="Scroll down to explore"
            >
              <span className="intro-scroll-text">Scroll to explore</span>
              <div className="intro-scroll-arrow">↓</div>
            </button>
          </div>
        </section>

        {/* Main Overview & Detailed Description Section */}
        <section id="overview" className="hero-section">
          <div className="hero-tag">
            <span>🤖</span>
            <span>6 AGENTS · LANGGRAPH STATE MACHINE · REAL PLACE DATA</span>
          </div>

          <h2 className="hero-title" style={{ textAlign: 'left', alignItems: 'flex-start' }}>
            <span className="title-regular">Tell it where you&apos;re going.</span>
            <span className="title-highlight gradient-text-hero">It handles everything else.</span>
          </h2>

          <p className="hero-subtitle" style={{ textAlign: 'left' }}>
            WanderAI runs a LangGraph pipeline: intake agent extracts your destination and dates,
            a planner agent fetches live place data from OpenTripMap and Google Places, a niche-scoring
            agent finds hidden gems using a log-normalized community sentiment formula, a geo-clustering
            agent groups stops into walk-friendly daily areas, and a narrator agent writes each stop.
          </p>

          <div className="hero-actions" style={{ justifyContent: 'flex-start' }}>
            <button
              className="btn-hero-primary"
              onClick={() => scrollToSection('planner-studio')}
            >
              <span>Try it — type any destination ↓</span>
            </button>
            <button
              className="btn-hero-secondary"
              onClick={() => scrollToSection('how-it-works')}
            >
              <span>See how it works</span>
            </button>
          </div>

          {/* Quick Start Prompt Cards */}
          <div className="hero-chips-container">
            <div className="hero-chips-label">Or launch a curated journey instantly</div>
            <div className="hero-chips-grid">
              {HERO_PROMPT_CARDS.map((card) => (
                <div
                  key={card.destination}
                  className="hero-prompt-card"
                  style={{ backgroundImage: `url(${card.image})` }}
                  onClick={() => handleHeroPromptSelect(card.prompt)}
                  title={`Generate itinerary for ${card.destination}`}
                >
                  <div className="hero-prompt-header">
                    <span className="hero-prompt-flag">{card.flag}</span>
                    <span style={{
                      fontSize: 10.5,
                      color: 'var(--amber)',
                      fontFamily: 'var(--font-label)',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      background: 'rgba(4, 14, 31, 0.75)',
                      padding: '3px 8px',
                      borderRadius: 'var(--radius-full)',
                      border: '1px solid var(--glass-border-amber)',
                    }}>
                      {card.tag}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                    <div className="hero-prompt-text">{card.destination}</div>
                    <span className="hero-prompt-arrow">➔</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Technical Facts Strip — real numbers only */}
          <div className="stats-strip">
            <div className="stat-item">
              <span className="stat-value">6</span>
              <span className="stat-label">Specialized AI Agents</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">3</span>
              <span className="stat-label">Live Data Sources (OTM · Places · Tavily)</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">K-Means</span>
              <span className="stat-label">Geo-Clustering · Walk-Optimized Days</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">LangGraph</span>
              <span className="stat-label">Deterministic State Machine Orchestration</span>
            </div>
          </div>
        </section>

        {/* How It Works & Architecture Section */}
        <section id="how-it-works" className="features-section">
          <div className="section-header">
            <span className="section-tag">TECHNICAL ARCHITECTURE</span>
            <h2 className="section-title">What happens after you hit send</h2>
            <p className="section-subtitle">
              A LangGraph state machine routes your message through six agents in parallel.
              Each agent has a single job — intake, discovery, niche-scoring, clustering, narration, or editing.
            </p>
          </div>

          <div className="features-grid">
            {/* Wide primary card — spans full grid width, 2-column interior layout */}
            <div className="feature-card amber-glow feature-card-wide">
              <div>
                <div className="feature-icon-box icon-box-amber">🤖</div>
                <h3 className="feature-title">Intake → Planner → Narrator pipeline</h3>
                <div className="feature-pill" style={{ marginTop: 16 }}>⚡ LangGraph · FastAPI · Python 3.11</div>
              </div>
              <div>
                <p className="feature-desc">
                  Your message hits the <strong>Intake Agent</strong> (Qwen 3.6 27B via Groq) which extracts
                  destination, dates, and style preferences. The <strong>Planner Agent</strong> fetches up to 200
                  candidates from OpenTripMap and Google Places in parallel. The <strong>Niche Scorer</strong> ranks
                  them by a log-normalized formula — high community sentiment × low review saturation = hidden gem.
                  Finally, <strong>Gemini 2.5 Flash</strong> writes atmospheric narrations for each stop.
                </p>
              </div>
            </div>

            <div className="feature-card teal-glow">
              <div className="feature-icon-box icon-box-teal">💎</div>
              <h3 className="feature-title">Hidden Gem Formula</h3>
              <p className="feature-desc">
                Score = log(community_mentions + 1) ÷ (google_review_count + 1).
                A café with 40 Reddit mentions but only 200 Google reviews ranks above
                a tourist trap with 12,000 reviews and no local conversation.
              </p>
              <div className="feature-pill">📊 Log-Normalized Ranking</div>
            </div>

            <div className="feature-card emerald-glow">
              <div className="feature-icon-box icon-box-emerald">🗺️</div>
              <h3 className="feature-title">Walk-Optimized Daily Areas</h3>
              <p className="feature-desc">
                Pure-Python k-means groups stops by GPS coordinates so each day
                stays within one neighbourhood — no zig-zagging across the city.
              </p>
              <div className="feature-pill">🧭 Spatial K-Means</div>
            </div>
          </div>
        </section>

        {/* Interactive Planning Studio Section */}
        <section id="planner-studio" className="studio-section">
          <div className="section-header" style={{ marginBottom: 36 }}>
            <span className="section-tag">INTERACTIVE STUDIO</span>
            <h2 className="section-title">Type a destination to begin</h2>
            <p className="section-subtitle">
              &quot;4 days in Kyoto, temples and ramen&quot; is enough. The agents fill in the rest.
            </p>
          </div>

          {/* Centered Conversational Planning Hub */}
          <div className="studio-centered-flow">
            <ErrorBoundary fallbackTitle="Chat Studio Error">
              <ChatPanel
                onItinerary={handleItineraryReceived}
                agentEvents={agentEvents}
                isStreaming={isStreaming}
                setAgentEvents={setAgentEvents}
                setIsStreaming={setIsStreaming}
                externalPrompt={externalPrompt}
                onExternalPromptConsumed={() => setExternalPrompt(null)}
                externalAction={externalAction}
                onExternalActionConsumed={() => setExternalAction(null)}
                externalEditInstruction={externalEditInstruction}
                onExternalEditInstructionConsumed={() => setExternalEditInstruction(null)}
              />
            </ErrorBoundary>
          </div>

          {/* Expansive Side-by-Side Itinerary & Map Visualizer */}
          {(itinerary || isStreaming) && (
            <div id="itinerary-visualizer" className="itinerary-full-wrapper" style={{ marginTop: 48 }}>
              <ErrorBoundary fallbackTitle="Itinerary Visualizer Error">
                <ItineraryView
                  itinerary={itinerary}
                  isLoading={isStreaming && !itinerary}
                  onStopAction={(req) => {
                    setExternalAction(req);
                    scrollToSection('planner-studio');
                  }}
                  onQuickEdit={(instruction) => {
                    setExternalEditInstruction(instruction);
                    scrollToSection('planner-studio');
                  }}
                />
              </ErrorBoundary>
            </div>
          )}
        </section>

        {/* Footer */}
        <footer className="site-footer">
          <div className="footer-content">
            <div className="footer-left">
              <div className="logo-mark" style={{ width: 32, height: 32, fontSize: 16 }}>🧭</div>
              <span className="logo-text" style={{ fontSize: 18 }}>WanderAI</span>
              <span className="footer-copy">© 2026 WanderAI. Versatile multi-agent AI travel planner.</span>
            </div>

            <div className="footer-tags">
              <span className="footer-tag">LangGraph</span>
              <span className="footer-tag">FastAPI</span>
              <span className="footer-tag">Groq Qwen3.6-27b</span>
              <span className="footer-tag">Gemini 2.5 Flash</span>
              <span className="footer-tag">Leaflet Dark Matter</span>
              <span className="footer-tag">Open-Meteo</span>
            </div>

            <a className="footer-back-top" onClick={() => scrollToSection('intro')}>
              Back to Top ↑
            </a>
          </div>
        </footer>

        {/* Mobile Sticky Bottom Navigation Bar */}
        <nav className="mobile-bottom-nav">
          <button
            type="button"
            className={`mobile-nav-btn ${activeMobileTab === 'studio' ? 'active' : ''}`}
            onClick={() => {
              setActiveMobileTab('studio');
              scrollToSection('planner-studio');
            }}
          >
            <span>💬</span>
            <span>Studio</span>
          </button>
          <button
            type="button"
            className={`mobile-nav-btn ${activeMobileTab === 'itinerary' ? 'active' : ''}`}
            onClick={() => {
              setActiveMobileTab('itinerary');
              const el = document.getElementById('itinerary-visualizer') || document.getElementById('planner-studio');
              if (el) el.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            <span>📋</span>
            <span>Itinerary</span>
          </button>
          <button
            type="button"
            className={`mobile-nav-btn ${activeMobileTab === 'history' ? 'active' : ''}`}
            onClick={() => {
              setActiveMobileTab('history');
              setIsHistoryOpen(true);
            }}
          >
            <span>🗂️</span>
            <span>History</span>
          </button>
          <button
            type="button"
            className={`mobile-nav-btn ${activeMobileTab === 'about' ? 'active' : ''}`}
            onClick={() => {
              setActiveMobileTab('about');
              scrollToSection('how-it-works');
            }}
          >
            <span>🧭</span>
            <span>Architecture</span>
          </button>
        </nav>
      </div>
    </ToastProvider>
  );
}
