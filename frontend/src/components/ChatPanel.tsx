'use client';

import { ChatMessage, AgentEvent, Itinerary, ClarificationQuestion, StopEditRequest } from '@/types';
import { useEffect, useRef, useState } from 'react';
import AgentEventFeed from './AgentEventFeed';

const PROMPT_CHIPS = [
  '3 days in Mumbai, coastal walks & heritage 🇮🇳',
  '3 days in Pune, Maratha forts & street food 🇮🇳',
  '3 days in Goa, beaches & heritage 🌴',
  '4 days in Rajasthan, royal forts & desert culture 👑',
];

const POPULAR_DESTINATIONS = [
  { name: 'Goa', icon: '🌴' },
  { name: 'Mumbai', icon: '🌆' },
  { name: 'Rajasthan', icon: '👑' },
  { name: 'Kashmir', icon: '🏔️' },
  { name: 'Kyoto', icon: '⛩️' },
  { name: 'Lisbon', icon: '🚋' },
  { name: 'Paris', icon: '🗼' },
];

const DURATION_OPTIONS = [1, 2, 3, 4, 5, 7, 10];

interface Props {
  onItinerary: (itinerary: Itinerary) => void;
  agentEvents: AgentEvent[];
  isStreaming: boolean;
  setAgentEvents: React.Dispatch<React.SetStateAction<AgentEvent[]>>;
  setIsStreaming: (v: boolean) => void;
  externalPrompt?: string | null;
  onExternalPromptConsumed?: () => void;
  externalAction?: StopEditRequest | null;
  onExternalActionConsumed?: () => void;
  /** Quick-edit instruction from ItineraryView chips — always edits the CURRENT itinerary */
  externalEditInstruction?: string | null;
  onExternalEditInstructionConsumed?: () => void;
}

export default function ChatPanel({
  onItinerary,
  agentEvents,
  isStreaming,
  setAgentEvents,
  setIsStreaming,
  externalPrompt,
  onExternalPromptConsumed,
  externalAction,
  onExternalActionConsumed,
  externalEditInstruction,
  onExternalEditInstructionConsumed,
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
  const [pendingTrip, setPendingTrip] = useState<{
    destination: string;
    num_days: number;
  } | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});

  // Phase 11A — Dual-Mode Intake & State Preservation
  const [inputMode, setInputMode] = useState<'chat' | 'guided'>('chat');
  const [guidedDestination, setGuidedDestination] = useState('');
  const [guidedDays, setGuidedDays] = useState(3);
  const [guidedStyles, setGuidedStyles] = useState<string[]>(['balanced']);
  const [guidedPace, setGuidedPace] = useState<'slow' | 'moderate' | 'fast'>('moderate');
  const [guidedBudget, setGuidedBudget] = useState<'budget' | 'moderate' | 'luxury'>('moderate');
  const [guidedGroup, setGuidedGroup] = useState<'solo' | 'couple' | 'family' | 'friends'>('solo');
  const [guidedInterests, setGuidedInterests] = useState<string[]>([]);

  // Bi-directional state sync: reflect chat trip extractions into guided builder
  useEffect(() => {
    const dest = pendingTrip?.destination || activeClarification?.destination;
    if (dest && dest !== 'Unknown' && !guidedDestination) {
      setGuidedDestination(dest);
    }
    const days = pendingTrip?.num_days || activeClarification?.num_days;
    if (days && days > 0) {
      setGuidedDays(days);
    }
  }, [pendingTrip, activeClarification]);

  const handleGuidedDestinationChange = (dest: string) => {
    setGuidedDestination(dest);
    setPendingTrip(prev => ({
      destination: dest,
      num_days: prev?.num_days || guidedDays,
    }));
  };

  const handleGuidedDaysChange = (days: number) => {
    setGuidedDays(days);
    setPendingTrip(prev => ({
      destination: prev?.destination || guidedDestination || 'Unknown',
      num_days: days,
    }));
  };

  const handleGuidedSubmit = () => {
    const dest = (guidedDestination || pendingTrip?.destination || 'Goa').trim();
    const days = guidedDays || pendingTrip?.num_days || 3;

    const styleLabels = guidedStyles.join(', ');
    const interestLabels = guidedInterests.length > 0 ? `interests: ${guidedInterests.join(', ')}` : '';
    const details = [styleLabels, interestLabels, `${guidedPace} pace`, `${guidedGroup} travel`]
      .filter(Boolean)
      .join('; ');

    const outgoingMessage = `${days} days in ${dest}${details ? ` (${details})` : ''}`;

    const customAnswers: Record<string, string> = {
      travel_style: guidedStyles[0] || 'balanced',
      pace: guidedPace,
      budget: guidedBudget,
      group_type: guidedGroup,
    };
    if (guidedInterests.length > 0) {
      customAnswers['interests'] = guidedInterests.join(', ');
    }

    handleSend(outgoingMessage, {
      customAnswers,
    });

    setInputMode('chat');
  };

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isFirstRender = useRef(true);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages, activeClarification]);

  // Handle external prompt triggers (e.g. from Hero destination chips — brand-new trip)
  useEffect(() => {
    if (externalPrompt && !isStreaming) {
      handleSend(externalPrompt);
      if (onExternalPromptConsumed) {
        onExternalPromptConsumed();
      }
    }
  }, [externalPrompt]); // eslint-disable-line react-hooks/exhaustive-deps

  // Handle quick-edit instruction chips from ItineraryView — must preserve existing_itinerary_id
  useEffect(() => {
    if (externalEditInstruction && !isStreaming) {
      handleSend(externalEditInstruction, { action: 'edit_whole' });
      if (onExternalEditInstructionConsumed) {
        onExternalEditInstructionConsumed();
      }
    }
  }, [externalEditInstruction]); // eslint-disable-line react-hooks/exhaustive-deps

  // Handle external stop quick actions (Swap, Remove, Tell Me More)
  useEffect(() => {
    if (externalAction && !isStreaming) {
      const act = externalAction.action;
      const stopName = externalAction.stop_name || 'stop';
      const dayNum = externalAction.day_number;

      let msg = '';
      if (act === 'swap') {
        msg = `Swap stop "${stopName}" on Day ${dayNum} for another attraction`;
      } else if (act === 'remove') {
        msg = `Remove "${stopName}" from Day ${dayNum}`;
      } else if (act === 'tell_me_more') {
        msg = `Tell me more about "${stopName}" on Day ${dayNum} and insider tips`;
      }

      handleSend(msg, {
        action: act,
        targetDay: dayNum,
        targetStopId: externalAction.stop_id,
        targetStopName: stopName,
      });

      if (onExternalActionConsumed) {
        onExternalActionConsumed();
      }
    }
  }, [externalAction]); // eslint-disable-line react-hooks/exhaustive-deps

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

  const [dietaryPreference, setDietaryPreference] = useState<string | null>(null);
  const [streamError, setStreamError] = useState<string | null>(null);
  const lastPromptRef = useRef<{ text?: string; options?: any }>({});

  const DIETARY_CHIPS = [
    { label: '🌱 Vegan', value: 'vegan' },
    { label: '🕌 Halal', value: 'halal' },
    { label: '🥗 Vegetarian', value: 'vegetarian' },
    { label: '🌾 Gluten-Free', value: 'gluten-free' },
    { label: '🕊️ Jain', value: 'jain' },
  ];

  const handleSend = async (
    textToSend?: string,
    options?: {
      forcePlan?: boolean;
      customAnswers?: Record<string, string>;
      action?: string;
      targetDay?: number;
      targetStopId?: string;
      targetStopName?: string;
    }
  ) => {
    let outgoingMessage = (textToSend !== undefined ? textToSend : input).trim();
    if (!outgoingMessage && !options?.forcePlan && !options?.customAnswers) return;

    lastPromptRef.current = { text: textToSend !== undefined ? textToSend : input, options };
    setStreamError(null);

    const explicitDest = pendingTrip?.destination || activeClarification?.destination;
    const explicitDays = pendingTrip?.num_days || activeClarification?.num_days;

    let finalAnswers = { ...(options?.customAnswers || selectedAnswers) };
    if (dietaryPreference) {
      finalAnswers['dietary'] = dietaryPreference;
    }

    if (options?.forcePlan) {
      const dest = explicitDest || 'Goa';
      const days = explicitDays || 3;
      outgoingMessage = `${days} days in ${dest}${dietaryPreference ? `, ${dietaryPreference} food` : ''}`;
      setMessages(prev => [...prev, { role: 'user', content: `⚡ Plan ${days} days in ${dest} with standard defaults` }]);
    } else if (options?.customAnswers) {
      const dest = explicitDest || 'Goa';
      const days = explicitDays || 3;
      const answerSummary = Object.values(options.customAnswers).join(', ');
      outgoingMessage = `${days} days in ${dest}${answerSummary ? `, ${answerSummary}` : ''}${dietaryPreference ? `, ${dietaryPreference}` : ''}`;
      setMessages(prev => [...prev, { role: 'user', content: `🚀 Plan ${days} days in ${dest} (${answerSummary})` }]);
    } else if (outgoingMessage) {
      if (dietaryPreference && !outgoingMessage.toLowerCase().includes(dietaryPreference)) {
        outgoingMessage += ` (${dietaryPreference} dining)`;
      }
      setInput('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
      setMessages(prev => [...prev, { role: 'user', content: outgoingMessage }]);
    }

    setActiveClarification(null);
    setAgentEvents([]);
    setIsStreaming(true);

    const abortController = new AbortController();
    const timeoutId = setTimeout(() => {
      abortController.abort();
    }, 90000); // 90 second safety watchdog for cold multi-agent generation

    try {
      const res = await fetch('http://localhost:8000/plan/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: abortController.signal,
        body: JSON.stringify({
          session_id: sessionId,
          message: outgoingMessage,
          destination: explicitDest,
          num_days: explicitDays,
          existing_itinerary_id: currentItineraryId,
          force_plan: options?.forcePlan || false,
          answers: finalAnswers,
          action: options?.action,
          target_day: options?.targetDay,
          target_stop_id: options?.targetStopId,
          target_stop_name: options?.targetStopName,
        }),
      });

      clearTimeout(timeoutId);

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
                const isExisting = Boolean(currentItineraryId);
                setCurrentItineraryId(parsed.id);
                onItinerary(parsed as Itinerary);
                setMessages(prev => [
                  ...prev,
                  {
                    role: 'assistant',
                    content: isExisting
                      ? `✨ I've updated your itinerary for **${parsed.trip_request.destination}**! The updated timeline and route are shown below.`
                      : `🎉 Your complete itinerary for **${parsed.trip_request.destination}** is ready below! Explore each day's curated route, interactive map pins, transit times, and weather forecast.`,
                  },
                ]);
              } else if (parsed.event_type === 'assistant_message' || ('message' in parsed && !parsed.event_type && !parsed.days)) {
                setMessages(prev => [
                  ...prev,
                  {
                    role: 'assistant',
                    content: parsed.message,
                  },
                ]);
              } else if (parsed.event_type === 'clarification_needed') {
                const questions = parsed.data?.questions as ClarificationQuestion[];
                const dest = (parsed.data?.destination as string) || '';
                const numDays = (parsed.data?.num_days as number) || 3;
                if (questions && questions.length > 0) {
                  setPendingTrip({ destination: dest, num_days: numDays });
                  setActiveClarification({
                    questions,
                    destination: dest,
                    num_days: numDays,
                  });
                  setMessages(prev => [
                    ...prev,
                    {
                      role: 'assistant',
                      content: parsed.message,
                      questions,
                      isClarification: true,
                      destination: dest,
                      num_days: numDays,
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
    } catch (err: any) {
      clearTimeout(timeoutId);
      const isAbort = err?.name === 'AbortError';
      const errMsg = isAbort
        ? 'Connection to planner timed out after 45 seconds.'
        : `Connection interrupted (${err.message || err}). Ensure backend is active at localhost:8000.`;
      setStreamError(errMsg);
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `⚠️ ${errMsg}` },
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

      {/* Top Mode Segmented Controller (Phase 11A) */}
      <div className="chat-mode-bar">
        <div className="chat-mode-segmented">
          <button
            type="button"
            className={`chat-mode-btn ${inputMode === 'chat' ? 'active' : ''}`}
            onClick={() => setInputMode('chat')}
            aria-pressed={inputMode === 'chat'}
          >
            <span className="mode-icon">💬</span>
            <span className="mode-label">Freeform Chat</span>
          </button>
          <button
            type="button"
            className={`chat-mode-btn ${inputMode === 'guided' ? 'active' : ''}`}
            onClick={() => setInputMode('guided')}
            aria-pressed={inputMode === 'guided'}
          >
            <span className="mode-icon">✨</span>
            <span className="mode-label">Guided Builder</span>
            <span className="mode-badge">Option-Based</span>
          </button>
        </div>

        <div className="chat-mode-hint">
          {inputMode === 'chat' ? (
            <span>Talk naturally with the 6-agent swarm</span>
          ) : (
            <span>Tailor trip dimensions visually with multi-select</span>
          )}
        </div>
      </div>

      {/* Dietary Filter Bar (Shared across both modes) */}
      <div style={{ padding: '8px 16px', background: 'rgba(4, 14, 31, 0.4)', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 11, fontFamily: 'var(--font-label)', color: 'var(--text-muted)', fontWeight: 600, marginRight: 2 }}>
          DIETARY BIAS:
        </span>
        {DIETARY_CHIPS.map((chip) => {
          const isSelected = dietaryPreference === chip.value;
          return (
            <button
              key={chip.value}
              type="button"
              onClick={() => setDietaryPreference(isSelected ? null : chip.value)}
              style={{
                background: isSelected ? 'rgba(0, 219, 231, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                border: `1px solid ${isSelected ? '#00DBE7' : 'rgba(255, 255, 255, 0.1)'}`,
                color: isSelected ? '#00DBE7' : 'var(--text-muted)',
                borderRadius: 'var(--radius-full, 9999px)',
                padding: '3px 9px',
                fontSize: 11,
                cursor: 'pointer',
                fontWeight: 600,
                transition: 'all 150ms',
              }}
              title={`Bias recommendations towards ${chip.label}`}
            >
              {chip.label}
            </button>
          );
        })}
      </div>

      {/* Mode A: Freeform Chat View */}
      {inputMode === 'chat' && (
        <>
          {/* Messages Scroll Area */}
          <div className="chat-messages-hub" ref={messagesContainerRef}>
            {messages.map((msg, i) => (
              <div key={i} className="message-wrapper">
                <div className={`chat-bubble ${msg.role}`}>
                  {msg.content.split('**').map((part, j) =>
                    j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                  )}

                  {/* Render Interactive Clarification Card inside the message if present */}
                  {msg.isClarification && msg.questions && (
                    <div className="clarification-card">
                      <div className="clarification-title">✨ Quick Travel Preferences for {msg.destination || 'your trip'}:</div>
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

            {/* Error / Timeout Banner */}
            {streamError && (
              <div
                style={{
                  margin: '8px 16px',
                  padding: '10px 14px',
                  background: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid rgba(239, 68, 68, 0.35)',
                  borderRadius: 8,
                  fontSize: 12.5,
                  color: '#fca5a5',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span>{streamError}</span>
                <button
                  type="button"
                  onClick={() => handleSend(lastPromptRef.current.text, lastPromptRef.current.options)}
                  style={{
                    background: '#ef4444',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 4,
                    padding: '4px 10px',
                    fontSize: 11.5,
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  Retry ↺
                </button>
              </div>
            )}
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
              placeholder="Where to? (e.g. '3 days in Mumbai' or '3 days in Pune, street food')"
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
        </>
      )}

      {/* Mode B: Guided Builder Framework Panel (Phase 11A) */}
      {inputMode === 'guided' && (
        <div className="guided-builder-container">
          {/* Destination Field Group */}
          <div className="guided-field-group">
            <div className="guided-field-label">
              <span>📍 Destination</span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'none', fontWeight: 400 }}>
                (Type or select a popular hub)
              </span>
            </div>
            <div className="guided-input-row">
              <input
                type="text"
                className="guided-text-input"
                placeholder="Where to? (e.g. Kashmir, Kyoto, Goa, Paris, Lisbon)"
                value={guidedDestination}
                onChange={(e) => handleGuidedDestinationChange(e.target.value)}
                disabled={isStreaming}
              />
            </div>
            <div className="guided-chips-row">
              {POPULAR_DESTINATIONS.map((dest) => {
                const isSelected = guidedDestination.toLowerCase() === dest.name.toLowerCase();
                return (
                  <button
                    key={dest.name}
                    type="button"
                    className={`guided-pill-btn ${isSelected ? 'active' : ''}`}
                    onClick={() => handleGuidedDestinationChange(dest.name)}
                    disabled={isStreaming}
                  >
                    <span>{dest.icon}</span>
                    <span>{dest.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Duration Field Group */}
          <div className="guided-field-group">
            <div className="guided-field-label">
              <span>🗓️ Trip Duration</span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'none', fontWeight: 400 }}>
                (Pacing optimized for each day)
              </span>
            </div>
            <div className="guided-chips-row">
              {DURATION_OPTIONS.map((days) => {
                const isSelected = guidedDays === days;
                return (
                  <button
                    key={days}
                    type="button"
                    className={`guided-pill-btn ${isSelected ? 'active' : ''}`}
                    onClick={() => handleGuidedDaysChange(days)}
                    disabled={isStreaming}
                  >
                    <span>{days} {days === 1 ? 'Day' : 'Days'}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Stream Error Banner */}
          {streamError && (
            <div
              style={{
                padding: '10px 14px',
                background: 'rgba(239, 68, 68, 0.12)',
                border: '1px solid rgba(239, 68, 68, 0.35)',
                borderRadius: 8,
                fontSize: 12.5,
                color: '#fca5a5',
              }}
            >
              {streamError}
            </div>
          )}

          {/* Live Agent Thought Feed (while streaming) */}
          <AgentEventFeed events={agentEvents} isStreaming={isStreaming} />

          {/* Action Bar Footer */}
          <div className="guided-builder-actions">
            <div className="guided-summary-pill">
              <span>Selected:</span>
              <strong style={{ color: '#fff' }}>
                {guidedDestination.trim() || 'Select destination'}
              </strong>
              <span>·</span>
              <span style={{ color: 'var(--teal)' }}>{guidedDays} Days</span>
              {dietaryPreference && (
                <>
                  <span>·</span>
                  <span style={{ color: 'var(--amber)' }}>{dietaryPreference}</span>
                </>
              )}
            </div>

            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <button
                type="button"
                className="prompt-chip"
                onClick={() => setInputMode('chat')}
                disabled={isStreaming}
              >
                💬 Open in Chat
              </button>

              <button
                type="button"
                className="chat-hub-send-btn"
                onClick={handleGuidedSubmit}
                disabled={!guidedDestination.trim() || isStreaming}
                style={{ height: 42, padding: '0 20px' }}
              >
                <span>🚀 Generate Itinerary</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
