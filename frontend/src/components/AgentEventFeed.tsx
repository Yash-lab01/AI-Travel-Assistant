'use client';

import { AgentEvent } from '@/types';
import { useEffect, useRef } from 'react';

const EVENT_ICONS: Record<AgentEvent['event_type'], string> = {
  agent_start:        '🚀',
  tool_call:          '🔧',
  tool_result:        '✅',
  agent_step:         '⚙️',
  narration_start:    '✨',
  narration_complete: '📝',
  itinerary_ready:    '🎉',
  error:              '❌',
};

const DOT_CLASS: Record<AgentEvent['event_type'], string> = {
  agent_start:        '',
  tool_call:          '',
  tool_result:        'done',
  agent_step:         '',
  narration_start:    '',
  narration_complete: 'done',
  itinerary_ready:    'done',
  error:              'error',
};

interface Props {
  events: AgentEvent[];
  isStreaming: boolean;
}

export default function AgentEventFeed({ events, isStreaming }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  if (!isStreaming && events.length === 0) {
    return (
      <div className="agent-feed" style={{ color: 'var(--text-muted)', fontSize: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ opacity: 0.6 }}>⚡</span>
        <span>Agent reasoning stream will appear here</span>
      </div>
    );
  }

  return (
    <div className="agent-feed">
      {events.map((ev, i) => (
        <div key={i} className="agent-event">
          <span className={`dot ${DOT_CLASS[ev.event_type]}`} />
          <span style={{ fontSize: 12 }}>{EVENT_ICONS[ev.event_type]}</span>
          <span>
            {ev.agent && <span style={{ color: 'var(--amber)', fontWeight: 600 }}>{ev.agent}</span>}
            {ev.tool && <span style={{ color: 'var(--teal)' }}> [{ev.tool}]</span>}
            {' '}{ev.message}
          </span>
        </div>
      ))}
      {isStreaming && (
        <div className="agent-event">
          <span className="dot" style={{ animation: 'pulseDot 1s infinite' }} />
          <span style={{ color: 'var(--text-muted)' }}>Multi-agent swarm reasoning...</span>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
