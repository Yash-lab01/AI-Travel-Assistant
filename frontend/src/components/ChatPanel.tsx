'use client';

import { ChatMessage } from '@/types';
import { useEffect, useRef, useState } from 'react';
import AgentEventFeed from './AgentEventFeed';
import { AgentEvent } from '@/types';

const PROMPT_CHIPS = [
  '3 days in Lisbon, hidden gems 🇵🇹',
  'Tokyo on a budget, mostly niche 🇯🇵',
  'Weekend in Medellín, couple 🇨🇴',
  'Solo trip to Kyoto, relaxed pace 🌸',
];

interface Props {
  onItinerary: (itinerary: unknown) => void;
  agentEvents: AgentEvent[];
  isStreaming: boolean;
  setAgentEvents: (events: AgentEvent[]) => void;
  setIsStreaming: (v: boolean) => void;
}

export default function ChatPanel({
  onItinerary,
  agentEvents,
  isStreaming,
  setAgentEvents,
  setIsStreaming,
}: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: "Hey! I'm your AI travel assistant. Tell me where you'd like to go — destination, how many days, your budget, and whether you prefer popular sights or hidden gems. I'll build a personalised itinerary for you. ✈️",
    },
  ]);
  const [input, setInput] = useState('');
  const [sessionId] = useState(() => crypto.randomUUID());
  const [currentItineraryId, setCurrentItineraryId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
  };

  const handleSend = async (text?: string) => {
    const message = (text ?? input).trim();
    if (!message || isStreaming) return;

    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    setMessages(prev => [...prev, { role: 'user', content: message }]);
    setAgentEvents([]);
    setIsStreaming(true);

    try {
      const res = await fetch('http://localhost:8000/plan/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message,
          existing_itinerary_id: currentItineraryId,
        }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (line.startsWith('event: agent_event')) continue;
          if (line.startsWith('data: ') && !line.includes('{}')) {
            const raw = line.slice(6).trim();
            if (!raw) continue;
            try {
              const parsed = JSON.parse(raw);
              // If it has 'days' it's an itinerary
              if ('days' in parsed) {
                setCurrentItineraryId(parsed.id);
                onItinerary(parsed);
                setMessages(prev => [
                  ...prev,
                  { role: 'assistant', content: `Your itinerary for **${parsed.trip_request.destination}** is ready! You can ask me to swap stops, adjust the pace, or change the budget. 🗺️` },
                ]);
              } else if ('event_type' in parsed) {
                setAgentEvents(prev => [...prev, parsed as AgentEvent]);
              }
            } catch { /* ignore parse errors */ }
          }
        }
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `Sorry, something went wrong. Make sure the backend is running at localhost:8000. (${err})` },
      ]);
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            {msg.content.split('**').map((part, j) =>
              j % 2 === 1 ? <strong key={j}>{part}</strong> : part
            )}
          </div>
        ))}
        {isStreaming && (
          <div className="chat-bubble assistant" style={{ opacity: 0.6 }}>
            <span className="dot" style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-teal)', marginRight: 6, animation: 'pulse 1.5s infinite' }} />
            Planning your trip...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <AgentEventFeed events={agentEvents} isStreaming={isStreaming} />

      <div className="chat-input-area">
        <textarea
          ref={textareaRef}
          className="chat-input"
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Where would you like to go? (Enter to send)"
          rows={1}
          disabled={isStreaming}
        />
        <button
          className="send-btn"
          onClick={() => handleSend()}
          disabled={!input.trim() || isStreaming}
          title="Send"
        >
          ➤
        </button>
      </div>

      {messages.length === 1 && (
        <div style={{ padding: '0 16px 12px', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {PROMPT_CHIPS.map(chip => (
            <button key={chip} className="prompt-chip" onClick={() => handleSend(chip)}>
              {chip}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
