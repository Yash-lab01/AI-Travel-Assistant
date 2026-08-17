'use client';

import { ChatMessage, AgentEvent, Itinerary } from '@/types';
import { useEffect, useRef, useState } from 'react';
import AgentEventFeed from './AgentEventFeed';

const PROMPT_CHIPS = [
  '4 days in Rajasthan, royal forts & palaces 🇮🇳',
  '3 days in Lisbon, iconic sights & hidden gems 🇵🇹',
  'Weekend in South Goa, beaches & cafes 🌴',
  'Solo trip to Kyoto, relaxed temples & ramen 🇯🇵',
];

interface Props {
  onItinerary: (itinerary: Itinerary) => void;
  agentEvents: AgentEvent[];
  isStreaming: boolean;
  setAgentEvents: React.Dispatch<React.SetStateAction<AgentEvent[]>>;
  setIsStreaming: (v: boolean) => void;
  externalPrompt?: string | null;
  onExternalPromptConsumed?: () => void;
}

export default function ChatPanel({
  onItinerary,
  agentEvents,
  isStreaming,
  setAgentEvents,
  setIsStreaming,
  externalPrompt,
  onExternalPromptConsumed,
}: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: "Hey! I'm your AI travel assistant. Tell me where you'd like to travel — destination, duration, budget, and travel style (iconic landmarks, authentic hidden gems, or a balanced mix). I'll build a tailored day-by-day itinerary with live AI reasoning. ✈️✨",
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

  // Handle external prompt triggers (e.g. from Hero chips)
  useEffect(() => {
    if (externalPrompt && !isStreaming) {
      handleSend(externalPrompt);
      if (onExternalPromptConsumed) {
        onExternalPromptConsumed();
      }
    }
  }, [externalPrompt]); // eslint-disable-line react-hooks/exhaustive-deps

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
              if ('days' in parsed) {
                setCurrentItineraryId(parsed.id);
                onItinerary(parsed as Itinerary);
                setMessages(prev => [
                  ...prev,
                  { role: 'assistant', content: `Your itinerary for **${parsed.trip_request.destination}** is ready! You can explore the map and day timeline on the right, or ask me to adjust pacing, change budget, or swap stops. 🗺️✨` },
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
          <div className="chat-bubble assistant" style={{ opacity: 0.85, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: 'var(--teal)', animation: 'pulseDot 1.2s infinite' }} />
            <span>Multi-Agent Swarm reasoning in progress...</span>
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
          placeholder="Where to? (e.g. 4 days in Rajasthan, royal forts or 3 days in Lisbon)"
          rows={1}
          disabled={isStreaming}
        />
        <button
          className="send-btn"
          onClick={() => handleSend()}
          disabled={!input.trim() || isStreaming}
          title="Send message"
        >
          ➤
        </button>
      </div>

      {messages.length === 1 && (
        <div style={{ padding: '0 16px 14px', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
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
