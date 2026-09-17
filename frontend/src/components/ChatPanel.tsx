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

const STYLE_OPTIONS = [
  { label: 'Iconic Landmarks', value: 'popular', icon: '🏛️' },
  { label: 'Hidden Gems', value: 'niche', icon: '💎' },
  { label: 'Cultural Heritage', value: 'cultural', icon: '🏰' },
  { label: 'Food & Night Markets', value: 'foodie', icon: '🍲' },
  { label: 'Scenic Nature', value: 'nature', icon: '🌿' },
  { label: 'Adventure & Outdoors', value: 'adventure', icon: '🏄' },
  { label: 'Relaxed Leisure', value: 'relaxed', icon: '🧘' },
];

const PACE_OPTIONS = [
  { label: 'Relaxed (2-3 stops/day)', value: 'slow', icon: '🧘' },
  { label: 'Moderate (4-5 stops/day)', value: 'moderate', icon: '⚡' },
  { label: 'Packed (6+ stops/day)', value: 'fast', icon: '🏃' },
];

const BUDGET_OPTIONS = [
  { label: 'Budget / Backpacker', value: 'budget', icon: '🪙' },
  { label: 'Mid-Range / Balanced', value: 'moderate', icon: '⚖️' },
  { label: 'Luxury / Premium', value: 'luxury', icon: '✨' },
];

const GROUP_OPTIONS = [
  { label: 'Solo Explorer', value: 'solo', icon: '🎒' },
  { label: 'Couple Getaway', value: 'couple', icon: '💑' },
  { label: 'Family with Kids', value: 'family', icon: '👨‍👩‍👧' },
  { label: 'Friends Crew', value: 'friends', icon: '👥' },
];

const INTEREST_OPTIONS = [
  { label: 'Photo Spots', value: 'photography', icon: '📸' },
  { label: 'Artisanal Cafes', value: 'cafes', icon: '☕' },
  { label: 'Beaches & Coast', value: 'beaches', icon: '🏖️' },
  { label: 'Local Bazaars', value: 'shopping', icon: '🛍️' },
  { label: 'Sunset Viewpoints', value: 'viewpoints', icon: '🌄' },
  { label: 'Museums & Art', value: 'museums', icon: '🎨' },
  { label: 'Street Food Trails', value: 'street_food', icon: '🍜' },
  { label: 'Heritage Walks', value: 'heritage_walks', icon: '🥾' },
];

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
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string[]>>({});

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

  const toggleGuidedStyle = (styleVal: string) => {
    setGuidedStyles(prev => {
      if (prev.includes(styleVal)) {
        if (prev.length === 1) return prev; // Keep at least one selected style
        return prev.filter(s => s !== styleVal);
      }
      return [...prev, styleVal];
    });
  };

  const toggleGuidedInterest = (interestVal: string) => {
    setGuidedInterests(prev => {
      if (prev.includes(interestVal)) {
        return prev.filter(i => i !== interestVal);
      }
      return [...prev, interestVal];
    });
  };

  const handleResetGuided = () => {
    setGuidedDestination('');
    setGuidedDays(3);
    setGuidedStyles(['popular', 'niche']);
    setGuidedPace('moderate');
    setGuidedBudget('moderate');
    setGuidedGroup('solo');
    setGuidedInterests([]);
    setDietaryPreference(null);
  };

  const handleGuidedSubmit = () => {
    const dest = (guidedDestination || pendingTrip?.destination || 'Goa').trim();
    const days = guidedDays || pendingTrip?.num_days || 3;

    const styleNames = STYLE_OPTIONS
      .filter(s => guidedStyles.includes(s.value))
      .map(s => s.label)
      .join(' & ');

    const interestNames = INTEREST_OPTIONS
      .filter(i => guidedInterests.includes(i.value))
      .map(i => i.label)
      .join(', ');

    const paceLabel = PACE_OPTIONS.find(p => p.value === guidedPace)?.label || `${guidedPace} pace`;
    const groupLabel = GROUP_OPTIONS.find(g => g.value === guidedGroup)?.label || `${guidedGroup} travel`;
    const budgetLabel = BUDGET_OPTIONS.find(b => b.value === guidedBudget)?.label || `${guidedBudget} budget`;

    const details = [
      styleNames ? `style: ${styleNames}` : '',
      interestNames ? `interests: ${interestNames}` : '',
      paceLabel,
      groupLabel,
      budgetLabel,
      dietaryPreference ? `${dietaryPreference} food` : '',
    ].filter(Boolean).join('; ');

    const outgoingMessage = `${days} days in ${dest} (${details})`;

    let primaryStyle = 'balanced';
    if (guidedStyles.includes('niche') && !guidedStyles.includes('popular')) {
      primaryStyle = 'niche';
    } else if (guidedStyles.includes('popular') && !guidedStyles.includes('niche')) {
      primaryStyle = 'popular';
    } else if (guidedStyles.includes('foodie')) {
      primaryStyle = 'foodie';
    } else if (guidedStyles.includes('cultural')) {
      primaryStyle = 'cultural';
    } else if (guidedStyles.includes('adventure')) {
      primaryStyle = 'adventure';
    } else if (guidedStyles.includes('relaxed')) {
      primaryStyle = 'relaxed';
    }

    const customAnswers: Record<string, string> = {
      travel_style: primaryStyle,
      pace: guidedPace,
      budget: guidedBudget,
      group_type: guidedGroup,
    };
    if (guidedInterests.length > 0) {
      customAnswers['interests'] = guidedInterests.join(', ');
    }
    if (guidedStyles.length > 0) {
      customAnswers['styles'] = guidedStyles.join(', ');
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

  const handleSelectChip = (questionCategory: string, value: string, isMultiSelect?: boolean) => {
    if (questionCategory === 'destination' && value) {
      setPendingTrip(prev => ({
        destination: value,
        num_days: prev?.num_days || 3,
      }));
      setGuidedDestination(value);
    }
    setSelectedAnswers(prev => {
      const existing = prev[questionCategory] || [];
      if (isMultiSelect) {
        if (existing.includes(value)) {
          return {
            ...prev,
            [questionCategory]: existing.filter(v => v !== value),
          };
        } else {
          return {
            ...prev,
            [questionCategory]: [...existing, value],
          };
        }
      } else {
        if (existing.includes(value)) {
          return {
            ...prev,
            [questionCategory]: [],
          };
        } else {
          return {
            ...prev,
            [questionCategory]: [value],
          };
        }
      }
    });
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
      customAnswers?: Record<string, string | string[]>;
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

    let finalAnswers: Record<string, string | string[]> = { ...(options?.customAnswers || selectedAnswers) };
    if (dietaryPreference) {
      finalAnswers['dietary'] = dietaryPreference;
    }

    const answerDest = Array.isArray(finalAnswers['destination']) ? finalAnswers['destination'][0] : finalAnswers['destination'];
    const explicitDest = answerDest || pendingTrip?.destination || activeClarification?.destination;
    const explicitDays = pendingTrip?.num_days || activeClarification?.num_days;

    if (options?.forcePlan) {
      const dest = explicitDest || 'Goa';
      const days = explicitDays || 3;
      const allSelectedValues: string[] = [];
      Object.values(finalAnswers).forEach(val => {
        if (Array.isArray(val)) {
          allSelectedValues.push(...val);
        } else if (typeof val === 'string' && val.trim() && val !== dest) {
          allSelectedValues.push(val);
        }
      });
      const summarySuffix = allSelectedValues.length > 0 ? ` (${allSelectedValues.join(', ')})` : '';
      outgoingMessage = `${days} days in ${dest}${allSelectedValues.length > 0 ? `, ${allSelectedValues.join(', ')}` : ''}${dietaryPreference ? `, ${dietaryPreference} food` : ''}`;
      setMessages(prev => [...prev, { role: 'user', content: `⚡ Generate ${days} days in ${dest} with given info${summarySuffix}` }]);
    } else if (options?.customAnswers) {
      const dest = explicitDest || 'Goa';
      const days = explicitDays || 3;
      const allSelectedValues: string[] = [];
      Object.values(options.customAnswers).forEach(val => {
        if (Array.isArray(val)) {
          allSelectedValues.push(...val);
        } else if (typeof val === 'string' && val.trim()) {
          allSelectedValues.push(val);
        }
      });
      const answerSummary = allSelectedValues.join(', ');
      outgoingMessage = `${days} days in ${dest}${answerSummary ? `, ${answerSummary}` : ''}${dietaryPreference ? `, ${dietaryPreference}` : ''}`;
      setMessages(prev => [...prev, { role: 'user', content: `🚀 Plan ${days} days in ${dest}${answerSummary ? ` (${answerSummary})` : ''}` }]);
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
              } else if (parsed.event_type === 'text_token' || ('chunk' in parsed && typeof parsed.chunk === 'string')) {
                const chunk = parsed.chunk;
                setMessages(prev => {
                  const last = prev[prev.length - 1];
                  if (last?.role === 'assistant' && last.isStreaming) {
                    return [...prev.slice(0, -1), { ...last, content: last.content + chunk }];
                  }
                  return [...prev, { role: 'assistant', content: chunk, isStreaming: true }];
                });
              } else if (parsed.event_type === 'assistant_message' || ('message' in parsed && !parsed.event_type && !parsed.days)) {
                setMessages(prev => {
                  const last = prev[prev.length - 1];
                  if (last?.role === 'assistant' && last.isStreaming) {
                    return [...prev.slice(0, -1), { ...last, content: parsed.message, isStreaming: false }];
                  }
                  return [
                    ...prev,
                    {
                      role: 'assistant',
                      content: parsed.message,
                    },
                  ];
                });
              } else if (parsed.event_type === 'done') {
                setMessages(prev => {
                  const hasStreaming = prev.some(m => m.isStreaming);
                  if (!hasStreaming) return prev;
                  return prev.map(m => (m.isStreaming ? { ...m, isStreaming: false } : m));
                });
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

      // Ensure all streaming flags are cleared once stream reader finishes
      setMessages(prev => {
        const hasStreaming = prev.some(m => m.isStreaming);
        if (!hasStreaming) return prev;
        return prev.map(m => (m.isStreaming ? { ...m, isStreaming: false } : m));
      });
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
      setMessages(prev => {
        const hasStreaming = prev.some(m => m.isStreaming);
        if (!hasStreaming) return prev;
        return prev.map(m => (m.isStreaming ? { ...m, isStreaming: false } : m));
      });
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
                <div className={`chat-bubble ${msg.role} ${msg.isStreaming ? 'chat-bubble-streaming' : ''}`}>
                  {msg.content.split('**').map((part, j) =>
                    j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                  )}

                  {/* Render Interactive Clarification Card inside the message if present */}
                  {msg.isClarification && msg.questions && (
                    <div className="clarification-card">
                      <div className="clarification-title">✨ Quick Travel Preferences for {msg.destination || 'your trip'}:</div>
                      {msg.questions.map((q) => {
                        const selectedVals = selectedAnswers[q.category] || [];
                        return (
                          <div key={q.id} className="clarification-question-group">
                            <div className="clarification-q-text">
                              {q.question}
                              {q.is_multi_select && (
                                <span className="clarification-multi-tag">Multi-select</span>
                              )}
                            </div>
                            <div className="clarification-options-grid">
                              {q.options.map((opt) => {
                                const isSelected = selectedVals.includes(opt.value);
                                return (
                                  <button
                                    key={opt.value}
                                    className={`clarification-option-chip ${isSelected ? 'selected' : ''}`}
                                    onClick={() => handleSelectChip(q.category, opt.value, q.is_multi_select)}
                                    disabled={isStreaming}
                                  >
                                    {isSelected && <span style={{ marginRight: 5, color: 'var(--teal)', fontWeight: 700 }}>✓</span>}
                                    {opt.icon && <span style={{ marginRight: 6 }}>{opt.icon}</span>}
                                    <span>{opt.label}</span>
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        );
                      })}

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
                          title="Generate immediately using standard defaults for any missing info"
                        >
                          <span>⚡ Generate Trip with Given Info (Defaults)</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Pre-stream typing indicator (Phase 12A) */}
            {isStreaming && !messages.some((m) => m.isStreaming) && (
              <div className="message-wrapper">
                <div className="chat-bubble assistant" style={{ display: 'inline-flex', alignItems: 'center', padding: '12px 18px' }}>
                  <div className="typing-indicator" aria-label="Assistant is typing">
                    <span className="dot" />
                    <span className="dot" />
                    <span className="dot" />
                  </div>
                </div>
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

          {/* Persistent Quick Action: Generate with Given Info (Phase 11E) */}
          {(pendingTrip?.destination || activeClarification?.destination || (guidedDestination && guidedDestination !== 'Unknown')) && !isStreaming && (
            <div className="chat-hub-instant-bar">
              <button
                type="button"
                className="btn-instant-generate"
                onClick={() => handleSend('', { forcePlan: true })}
                disabled={isStreaming}
              >
                <span className="instant-bolt">⚡</span>
                <span>Generate Trip with Given Info for <strong>{pendingTrip?.destination || activeClarification?.destination || guidedDestination}</strong></span>
                <span className="instant-badge">{pendingTrip?.num_days || activeClarification?.num_days || guidedDays} Days</span>
              </button>
            </div>
          )}

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

          {/* Travel Style & Vibe (Multi-select) */}
          <div className="guided-field-group">
            <div className="guided-field-label">
              <span>✨ Travel Style & Vibe</span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'none', fontWeight: 400 }}>
                (Multi-select · pick all that match your mood)
              </span>
            </div>
            <div className="guided-chips-row">
              {STYLE_OPTIONS.map((style) => {
                const isSelected = guidedStyles.includes(style.value);
                return (
                  <button
                    key={style.value}
                    type="button"
                    className={`guided-pill-btn ${isSelected ? 'active' : ''}`}
                    onClick={() => toggleGuidedStyle(style.value)}
                    disabled={isStreaming}
                  >
                    <span>{style.icon}</span>
                    <span>{style.label}</span>
                    {isSelected && <span className="check-mark">✓</span>}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Daily Sightseeing Pace */}
          <div className="guided-field-group">
            <div className="guided-field-label">
              <span>⚡ Daily Sightseeing Pace</span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'none', fontWeight: 400 }}>
                (Controls stop count and breathing room)
              </span>
            </div>
            <div className="guided-chips-row">
              {PACE_OPTIONS.map((p) => {
                const isSelected = guidedPace === p.value;
                return (
                  <button
                    key={p.value}
                    type="button"
                    className={`guided-pill-btn ${isSelected ? 'active' : ''}`}
                    onClick={() => setGuidedPace(p.value as any)}
                    disabled={isStreaming}
                  >
                    <span>{p.icon}</span>
                    <span>{p.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Two-Column: Budget & Companions */}
          <div className="guided-two-col">
            {/* Budget Tier */}
            <div className="guided-field-group">
              <div className="guided-field-label">
                <span>🪙 Budget Tier</span>
              </div>
              <div className="guided-chips-row">
                {BUDGET_OPTIONS.map((b) => {
                  const isSelected = guidedBudget === b.value;
                  return (
                    <button
                      key={b.value}
                      type="button"
                      className={`guided-pill-btn ${isSelected ? 'active' : ''}`}
                      onClick={() => setGuidedBudget(b.value as any)}
                      disabled={isStreaming}
                    >
                      <span>{b.icon}</span>
                      <span>{b.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Travel Companions */}
            <div className="guided-field-group">
              <div className="guided-field-label">
                <span>👥 Who's Traveling</span>
              </div>
              <div className="guided-chips-row">
                {GROUP_OPTIONS.map((g) => {
                  const isSelected = guidedGroup === g.value;
                  return (
                    <button
                      key={g.value}
                      type="button"
                      className={`guided-pill-btn ${isSelected ? 'active' : ''}`}
                      onClick={() => setGuidedGroup(g.value as any)}
                      disabled={isStreaming}
                    >
                      <span>{g.icon}</span>
                      <span>{g.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Must-Have Experiences & Interests (Multi-select) */}
          <div className="guided-field-group">
            <div className="guided-field-label">
              <span>🎯 Must-Have Activities & Interests</span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'none', fontWeight: 400 }}>
                (Multi-select · priorities for the route)
              </span>
            </div>
            <div className="guided-chips-row">
              {INTEREST_OPTIONS.map((item) => {
                const isSelected = guidedInterests.includes(item.value);
                return (
                  <button
                    key={item.value}
                    type="button"
                    className={`guided-pill-btn ${isSelected ? 'active' : ''}`}
                    onClick={() => toggleGuidedInterest(item.value)}
                    disabled={isStreaming}
                  >
                    <span>{item.icon}</span>
                    <span>{item.label}</span>
                    {isSelected && <span className="check-mark">✓</span>}
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
              <span>·</span>
              <span style={{ color: '#93c5fd' }}>
                {guidedStyles.length} {guidedStyles.length === 1 ? 'Style' : 'Styles'}
              </span>
              <span>·</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                {PACE_OPTIONS.find(p => p.value === guidedPace)?.label.split(' ')[0]} Pace
              </span>
              <span>·</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                {GROUP_OPTIONS.find(g => g.value === guidedGroup)?.label.split(' ')[0]}
              </span>
              {guidedInterests.length > 0 && (
                <>
                  <span>·</span>
                  <span style={{ color: '#c084fc' }}>
                    {guidedInterests.length} {guidedInterests.length === 1 ? 'Activity' : 'Activities'}
                  </span>
                </>
              )}
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
                className="guided-reset-btn"
                onClick={handleResetGuided}
                disabled={isStreaming}
                title="Reset preferences to default"
              >
                ↺ Reset
              </button>

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
