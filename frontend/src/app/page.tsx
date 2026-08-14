'use client';

import { useState } from 'react';
import ChatPanel from '@/components/ChatPanel';
import ItineraryView from '@/components/ItineraryView';
import { AgentEvent, Itinerary } from '@/types';

export default function Home() {
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [agentEvents, setAgentEvents] = useState<AgentEvent[]>([]);

  return (
    <div className="app-shell">
      {/* Header */}
      <header className="app-header">
        <div className="logo-mark">✈</div>
        <h1>AI Travel Assistant</h1>
        <span className="badge">Multi-Agent</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 12, alignItems: 'center' }}>
          {itinerary && (
            <button
              onClick={() => window.open(`http://localhost:8000/export/pdf/${itinerary.id}`, '_blank')}
              style={{
                background: 'transparent',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-secondary)',
                padding: '4px 12px',
                fontSize: 12,
                cursor: 'pointer',
                transition: 'all 200ms',
              }}
              onMouseEnter={e => {
                (e.target as HTMLButtonElement).style.borderColor = 'var(--accent-gold)';
                (e.target as HTMLButtonElement).style.color = 'var(--accent-gold)';
              }}
              onMouseLeave={e => {
                (e.target as HTMLButtonElement).style.borderColor = 'var(--border)';
                (e.target as HTMLButtonElement).style.color = 'var(--text-secondary)';
              }}
            >
              ⬇ Export PDF
            </button>
          )}
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            Gemini 2.5 Flash · Groq · LoRA
          </span>
        </div>
      </header>

      {/* Left: Chat */}
      <ChatPanel
        onItinerary={(it) => setItinerary(it as Itinerary)}
        agentEvents={agentEvents}
        isStreaming={isStreaming}
        setAgentEvents={setAgentEvents}
        setIsStreaming={setIsStreaming}
      />

      {/* Right: Itinerary */}
      <ItineraryView
        itinerary={itinerary}
        isLoading={isStreaming && !itinerary}
      />
    </div>
  );
}
