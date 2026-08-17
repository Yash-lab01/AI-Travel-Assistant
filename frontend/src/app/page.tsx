'use client';

import { useState } from 'react';
import ChatPanel from '@/components/ChatPanel';
import ItineraryView from '@/components/ItineraryView';
import TravelLiveWallpaper from '@/components/TravelLiveWallpaper';
import { AgentEvent, Itinerary } from '@/types';


const HERO_PROMPT_CARDS = [
  {
    flag: '🇵🇹',
    destination: 'Lisbon, Portugal',
    prompt: '3 days in Lisbon, hidden gems & authentic Fado',
    tag: 'Culture & Miradouros',
  },
  {
    flag: '🇯🇵',
    destination: 'Kyoto, Japan',
    prompt: '4 days in Kyoto, tranquil zen temples & local ramen',
    tag: 'Zen & Gastronomy',
  },
  {
    flag: '🇮🇸',
    destination: 'Reykjavik, Iceland',
    prompt: '5 days in Reykjavik, volcanic sights, hot springs & northern lights',
    tag: 'Nordic Adventure',
  },
  {
    flag: '🇲🇽',
    destination: 'Oaxaca, Mexico',
    prompt: '3 days in Oaxaca, culinary secrets, mezcal & artisan markets',
    tag: 'Artisan Culinary',
  },
];

export default function Home() {
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [agentEvents, setAgentEvents] = useState<AgentEvent[]>([]);
  const [externalPrompt, setExternalPrompt] = useState<string | null>(null);

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
    <>
      {/* Travel-Themed Live Wallpaper Canvas */}
      <TravelLiveWallpaper />

      <div className="main-wrapper">

        {/* Navigation Bar */}
        <header className="site-header">
          <div className="header-left">
            <div className="logo-group" onClick={() => scrollToSection('hero')}>
              <div className="logo-mark">🧭</div>
              <span className="logo-text">WanderAI</span>
            </div>
            <div className="badge">
              <span className="live-dot" />
              <span>Multi-Agent Swarm</span>
            </div>
          </div>

          <nav className="nav-links">
            <a className="nav-link" onClick={() => scrollToSection('hero')}>Overview</a>
            <a className="nav-link" onClick={() => scrollToSection('how-it-works')}>Architecture</a>
            <a className="nav-link" onClick={() => scrollToSection('planner-studio')}>Interactive Studio</a>
          </nav>

          <div className="header-right">
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

        {/* Hero Section */}
        <section id="hero" className="hero-section">
          <div className="hero-tag">
            <span>✨</span>
            <span>AUTONOMOUS TRAVEL INTELLIGENCE · POWERED BY LANGGRAPH</span>
          </div>

          <h1 className="hero-title">
            <span className="title-regular">Uncover the World's</span>
            <span className="title-highlight">Best Kept Secrets.</span>
          </h1>

          <p className="hero-subtitle">
            An intelligent multi-agent travel companion that discovers authentic hidden gems,
            balances local secrets with iconic landmarks, and builds geo-clustered daily itineraries
            in real-time through live AI reasoning.
          </p>

          <div className="hero-actions">
            <button
              className="btn-hero-primary"
              onClick={() => scrollToSection('planner-studio')}
            >
              <span>Start Planning Your Journey ↓</span>
            </button>
            <button
              className="btn-hero-secondary"
              onClick={() => scrollToSection('how-it-works')}
            >
              <span>Explore The Architecture</span>
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
                  onClick={() => handleHeroPromptSelect(card.prompt)}
                  title={`Generate itinerary for ${card.destination}`}
                >
                  <span className="hero-prompt-flag">{card.flag}</span>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--amber)', fontFamily: 'var(--font-label)', fontWeight: 600 }}>
                      {card.tag}
                    </div>
                    <div className="hero-prompt-text">{card.destination}</div>
                  </div>
                  <span className="hero-prompt-arrow">➔</span>
                </div>
              ))}
            </div>
          </div>

          {/* Live Metrics / Stats Strip */}
          <div className="stats-strip">
            <div className="stat-item">
              <span className="stat-value">85%</span>
              <span className="stat-label">Hidden Gem Discovery Ratio</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">&lt; 2s</span>
              <span className="stat-label">Multi-Agent Parallel Orchestration</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">100%</span>
              <span className="stat-label">Geo-Clustered Spatial Efficiency</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">Zero</span>
              <span className="stat-label">Sponsored Tourist Traps</span>
            </div>
          </div>
        </section>

        {/* How It Works & Architecture Section */}
        <section id="how-it-works" className="features-section">
          <div className="section-header">
            <span className="section-tag">ENGINEERED FOR AUTHENTICITY</span>
            <h2 className="section-title">How Multi-Agent Intelligence Works</h2>
            <p className="section-subtitle">
              Traditional travel apps push sponsored tourist traps. WanderAI coordinates
              specialized AI agents to cross-reference live place data, community sentiment, and spatial geometry.
            </p>
          </div>

          <div className="features-grid">
            <div className="feature-card amber-glow">
              <div className="feature-icon-box icon-box-amber">🤖</div>
              <h3 className="feature-title">Autonomous Agent Swarm</h3>
              <p className="feature-desc">
                A deterministic LangGraph state machine orchestrating Intake slot-filling (Groq Llama 3.1 8B),
                live OpenTripMap discovery, and thematic storytelling (Gemini 2.5 Flash) without hallucination loops.
              </p>
              <div className="feature-pill">⚡ LangGraph Orchestration</div>
            </div>

            <div className="feature-card teal-glow">
              <div className="feature-icon-box icon-box-teal">💎</div>
              <h3 className="feature-title">Hidden Gem Scoring Formula</h3>
              <p className="feature-desc">
                Our log-normalized formula cross-references Reddit & local travel blog sentiment against
                Google Places review saturation to rank authentically under-the-radar cultural spots.
              </p>
              <div className="feature-pill">📊 Log-Normalized Math</div>
            </div>

            <div className="feature-card emerald-glow">
              <div className="feature-icon-box icon-box-emerald">🗺️</div>
              <h3 className="feature-title">Geo-Clustering & Pacing</h3>
              <p className="feature-desc">
                Pure-Python k-means coordinate clustering groups attractions into seamless, walking-optimized
                daily clusters, eliminating exhausting zig-zagging across foreign cities.
              </p>
              <div className="feature-pill">🧭 Spatial K-Means</div>
            </div>
          </div>
        </section>

        {/* Interactive Planning Studio Section */}
        <section id="planner-studio" className="studio-section">
          <div className="section-header" style={{ marginBottom: 36 }}>
            <span className="section-tag">LIVE INTERACTIVE WORKSPACE</span>
            <h2 className="section-title">Design Your Personalized Itinerary</h2>
            <p className="section-subtitle">
              Chat with our multi-agent system below or customize pacing, budget, and hidden gem weight in real-time.
            </p>
          </div>

          <div className="studio-wrapper">
            {/* Left: Conversational Agent Panel */}
            <ChatPanel
              onItinerary={(it) => setItinerary(it)}
              agentEvents={agentEvents}
              isStreaming={isStreaming}
              setAgentEvents={setAgentEvents}
              setIsStreaming={setIsStreaming}
              externalPrompt={externalPrompt}
              onExternalPromptConsumed={() => setExternalPrompt(null)}
            />

            {/* Right: Itinerary & Map Visualizer */}
            <ItineraryView
              itinerary={itinerary}
              isLoading={isStreaming && !itinerary}
            />
          </div>
        </section>

        {/* Footer */}
        <footer className="site-footer">
          <div className="footer-content">
            <div className="footer-left">
              <div className="logo-mark" style={{ width: 32, height: 32, fontSize: 16 }}>🧭</div>
              <span className="logo-text" style={{ fontSize: 18 }}>WanderAI</span>
              <span className="footer-copy">© 2026 WanderAI. Autonomous multi-agent travel planner.</span>
            </div>

            <div className="footer-tags">
              <span className="footer-tag">LangGraph</span>
              <span className="footer-tag">FastAPI</span>
              <span className="footer-tag">Groq Llama 3.1</span>
              <span className="footer-tag">Gemini 2.5 Flash</span>
              <span className="footer-tag">ChromaDB</span>
              <span className="footer-tag">Mapbox GL JS</span>
            </div>

            <a className="footer-back-top" onClick={() => scrollToSection('hero')}>
              Back to Top ↑
            </a>
          </div>
        </footer>
      </div>
    </>
  );
}
