'use client';

import { ChatMessage, AgentEvent, Itinerary, ClarificationQuestion } from '@/types';
import { useEffect, useRef, useState } from 'react';
import AgentEventFeed from './AgentEventFeed';

const PROMPT_CHIPS = [
  '3 days in Goa, beaches & heritage 🌴',
  '4 days in Rajasthan, royal forts & desert culture 👑',
  '3 days in Lisbon, iconic sights & hidden gems 🇵🇹',
  '4 days in Kyoto, zen temples & local ramen 🇯🇵',
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
      content: "Hey! Where would you like to travel? Tell me your destination, duration, budget, and travel vibe (popular landmarks, authentic hidden gems, or a balanced blend). I'll craft a complete day-by-day itinerary tailored to you. ✈️✨",
    },
  ]);
  const [input, setInput] = useState('');
  const [sessionId] = useState(() => crypto.randomUUID());
  const [currentItineraryId, setCurrentItineraryId] = useState<string | null>(null);
  const [activeClarification, setActiveClarification] = useState<{
    questions: ClarificationQuestion[];
    destination?: string;
    num_days?: number;
  } | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isFirstRender = useRef(true);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeClarification]);


  // Handle external prompt triggers (e.g. from Hero chips)
  useEffect(() => {
    if (externalPrompt && !isStreaming) {
      handleSend(externalPrompt);
      if (onExternalPromptConsumed) {
        onExternalPromptConsumed();
      }
    }
  }, [externalPrompt]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
  };

  const handleSelectChip = (questionCategory: string, value: string) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionCategory]: value,
    }));
  };

  const handleSend = async (
    text?: string,
    options?: { forcePlan?: boolean; customAnswers?: Record<string, string> }
  ) => {
    const message = (text ?? input).trim();
    if (!message && !options?.forcePlan && !options?.customAnswers) return;

    const outgoingMessage = message || (options?.forcePlan ? 'Plan with standard defaults' : 'Submit preferences');

    if (!options?.forcePlan && !options?.customAnswers) {
      setInput('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
      setMessages(prev => [...prev, { role: 'user', content: outgoingMessage }]);
    }

    setActiveClarification(null);
    setAgentEvents([]);
    setIsStreaming(true);

    try {
      const res = await fetch('http://localhost:8000/plan/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: outgoingMessage,
          existing_itinerary_id: currentItineraryId,
          force_plan: options?.forcePlan || false,
          answers: options?.customAnswers || selectedAnswers,
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
                  {
                    role: 'assistant',
                    content: `🎉 Your complete itinerary for **${parsed.trip_request.destination}** is ready below! Explore each day's curated route, interactive map pins, transit times, and weather forecast.`,
                  },
                ]);
              } else if (parsed.event_type === 'clarification_needed') {
                const questions = parsed.data?.questions as ClarificationQuestion[];
                if (questions && questions.length > 0) {
                  setActiveClarification({
                    questions,
                    destination: parsed.data?.destination,
                    num_days: parsed.data?.num_days,
                  });
                  setMessages(prev => [
                    ...prev,
                    {
                      role: 'assistant',
                      content: parsed.message,
                      questions,
                      isClarification: true,
                      destination: parsed.data?.destination,
                      num_days: parsed.data?.num_days,
                    },
                  ]);
                }
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
    <div className="chat-hub-container">
      {/* Header Strip */}
      <div className="chat-hub-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="logo-mark" style={{ width: 28, height: 28, fontSize: 14 }}>🧭</div>
          <span style={{ fontFamily: 'var(--font-heading)', fontSize: 16, color: '#fff', fontWeight: 600 }}>
            WanderAI Planning Studio
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-muted)' }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--teal)', display: 'inline-block' }} />
          <span>Multi-Agent Swarm Ready</span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="chat-messages-hub">
        {messages.map((msg, i) => (
          <div key={i} className="message-wrapper">
            <div className={`chat-bubble ${msg.role}`}>
              {msg.content.split('**').map((part, j) =>
                j % 2 === 1 ? <strong key={j}>{part}</strong> : part
              )}

              {/* Render Interactive Clarification Card inside the message if present */}
              {msg.isClarification && msg.questions && (
                <div className="clarification-card">
                  <div className="clarification-title">✨ Quick Travel Preferences:</div>
                  {msg.questions.map((q) => (
                    <div key={q.id} className="clarification-question-group">
                      <div className="clarification-q-text">{q.question}</div>
                      <div className="clarification-options-grid">
                        {q.options.map((opt) => {
                          const isSelected = selectedAnswers[q.category] === opt.value;
                          return (
                            <button
                              key={opt.value}
                              className={`clarification-option-chip ${isSelected ? 'selected' : ''}`}
                              onClick={() => handleSelectChip(q.category, opt.value)}
                              disabled={isStreaming}
                            >
                              {opt.icon && <span style={{ marginRight: 6 }}>{opt.icon}</span>}
                              <span>{opt.label}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))}

                  {/* Action Buttons for Clarification */}
                  <div className="clarification-actions-row">
                    <button
                      className="btn-plan-preferences"
                      onClick={() => handleSend('', { customAnswers: selectedAnswers })}
                      disabled={isStreaming}
                    >
                      <span>🚀 Plan With Selected Preferences</span>
                    </button>
                    <button
                      className="btn-plan-defaults"
                      onClick={() => handleSend('', { forcePlan: true })}
                      disabled={isStreaming}
                    >
                      <span>⚡ Plan with defaults now</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {isStreaming && (
          <div className="chat-bubble assistant" style={{ opacity: 0.9, display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: 'var(--teal)', animation: 'pulseDot 1.2s infinite' }} />
            <span>Multi-Agent reasoning in progress (scoring, routing & weather)...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Live Agent Thought Feed */}
      <AgentEventFeed events={agentEvents} isStreaming={isStreaming} />

      {/* Input Form Area */}
      <div className="chat-hub-input-bar">
        <textarea
          ref={textareaRef}
          className="chat-hub-textarea"
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Where to? (e.g. '3 days in Goa' or '4 days in Rajasthan, royal forts')"
          rows={1}
          disabled={isStreaming}
        />
        <button
          className="chat-hub-send-btn"
          onClick={() => handleSend()}
          disabled={!input.trim() || isStreaming}
          title="Send message"
        >
          <span>Send</span>
          <span style={{ fontSize: 14 }}>➔</span>
        </button>
      </div>

      {/* Starter Prompt Chips */}
      {messages.length === 1 && (
        <div className="chat-hub-chips-row">
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
