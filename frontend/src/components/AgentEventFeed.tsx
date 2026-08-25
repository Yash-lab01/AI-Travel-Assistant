'use client';

import { AgentEvent } from '@/types';
import { useEffect, useRef } from 'react';

const EVENT_ICONS: Record<AgentEvent['event_type'], string> = {
  agent_start:          '🚀',
  tool_call:            '🔍',
  tool_result:          '✓',
  agent_step:           '⚡',
  clarification_needed: '💬',
  day_ready:            '📅',
  narration_start:      '✍️',
  narration_complete:   '✨',
  itinerary_ready:      '🎉',
  assistant_message:    '💬',
  error:                '⚠️',
};

const DOT_CLASS: Record<AgentEvent['event_type'], string> = {
  agent_start:          '',
  tool_call:            '',
  tool_result:          'done',
  agent_step:           '',
  clarification_needed: '',
  day_ready:            'done',
  narration_start:      '',
  narration_complete:   'done',
  itinerary_ready:      'done',
  assistant_message:    'done',
  error:                'error',
};

interface Props {
  events: AgentEvent[];
  isStreaming: boolean;
}

export default function AgentEventFeed({ events, isStreaming }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (events.length > 0 && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events]);

  if (!isStreaming && events.length === 0) {
    return (
      <div className="agent-feed-container" style={{ color: 'var(--text-muted)', fontSize: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ opacity: 0.6 }}>⚡</span>
        <span>Agent reasoning stream will appear here</span>
      </div>
    );
  }

  return (
    <div className="agent-feed-container" ref={containerRef}>
      {events.map((ev, i) => (
        <div key={i} className="agent-event-item">
          <span style={{ fontSize: 12 }}>{EVENT_ICONS[ev.event_type] || '⚡'}</span>
          <span>
            {ev.agent && <span style={{ color: 'var(--amber)', fontWeight: 600 }}>{ev.agent}</span>}
            {ev.tool && <span style={{ color: 'var(--teal)' }}> [{ev.tool}]</span>}
            {' '}{ev.message}
          </span>
        </div>
      ))}
      {isStreaming && (
        <div className="agent-event-item">
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--teal)', display: 'inline-block', animation: 'pulseDot 1s infinite' }} />
          <span style={{ color: 'var(--text-muted)' }}>Multi-agent swarm reasoning...</span>
        </div>
      )}
    </div>
  );
}
