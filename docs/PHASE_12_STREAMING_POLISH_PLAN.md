# Phase 12: UX Refinement, Streaming Polish & Performance

> **Status**: Planned 📋  
> **Date**: September 2026  
> **Author**: Antigravity AI Engineering & UX Architecture

---

## 1. Problem Statement & Motivation

After completing Phase 11 (Dual-Mode Intake & Multi-Select Planning Studio), several UX friction points remain:

1. **Text Pop-In**: When the LLM generates a clarification response or conversational reply, the entire text appears at once as a single block. This feels robotic compared to ChatGPT/Claude, which stream tokens progressively.
2. **Silent Pre-Stream Gap**: Between the user clicking Send and the first SSE event arriving (1–4 seconds of LangGraph routing + LLM cold start), there is dead silence — no indication the system is processing.
3. **Chat Feels Text-Heavy**: Clarification cards are pure text. Adding a destination photo inline makes the experience feel like a travel tool, not a form.
4. **Token Waste**: Several agents send unnecessarily long context to the LLM — niche scraper snippet lists, full `assistant_reply` system prompts with repetitive instructions, full itinerary JSON in edit state.
5. **Frontend Re-Renders**: `ChatPanel` rebuilds static arrays and closures on every render due to missing memoization.

---

## 2. Architecture: Current vs Target SSE Flow

### Current (main.py)
```
POST /plan/stream
  → await travel_graph.ainvoke(state)   ← BLOCKING: full graph runs first
  → replay stored events one by one     ← already done, just streaming the log
  → emit assistant_message (full text)  ← single emit, text pops in all at once
  → emit itinerary
  → emit done
```

### Target After Phase 12A
```
POST /plan/stream
  → graph runs to completion (ainvoke)
  → replay agent_event log
  → if assistant_reply: stream word-by-word via text_token events (18ms/word)
  → emit itinerary (if any)
  → emit done
```

> **Note**: Start with word-by-word replay (simpler, zero agent changes). The full real-time `astream_events()` upgrade can follow in a future iteration.

---

## 3. Phase 12A — LLM Chat Streaming (Token-by-Token)

### Backend Change — main.py
Replace the single `assistant_message` emit with word-by-word `text_token` streaming:

```python
if assistant_reply:
    words = assistant_reply.split(" ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        yield f"event: text_token\ndata: {json.dumps({'chunk': chunk})}\n\n"
        await asyncio.sleep(0.018)   # ~55 words/sec — feels natural
    # Also emit the full message for any backward-compat consumers
    yield f"event: assistant_message\ndata: {json.dumps({'message': assistant_reply})}\n\n"
```

### Frontend Change — ChatPanel.tsx
Add `text_token` event handler in the SSE reader loop:

```typescript
// In handleSend SSE reader:
} else if (eventType === 'text_token') {
  const { chunk } = parsed;
  setMessages(prev => {
    const last = prev[prev.length - 1];
    if (last?.role === 'assistant' && last.isStreaming) {
      // Append chunk to existing in-progress bubble
      return [...prev.slice(0, -1), { ...last, content: last.content + chunk }];
    }
    // First token: create the streaming bubble
    return [...prev, { role: 'assistant', content: chunk, isStreaming: true }];
  });
}
```

On `done` event: mark the last `isStreaming: true` message as `isStreaming: false`.

### Type Update — types/index.ts
```typescript
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;      // true while tokens accumulating
  clarificationData?: ClarificationQuestion[];
}
```

### CSS — globals.css
```css
/* Blinking cursor on in-progress message */
.chat-bubble-streaming::after {
  content: '|';
  display: inline-block;
  animation: blink 0.8s step-start infinite;
  color: var(--teal);
  margin-left: 2px;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
```

---

## 4. Phase 12A — Pre-Stream Typing Indicator

Show animated three-dot bubble immediately when `isStreaming = true`, before any `text_token` arrives:

```tsx
{isStreaming && !hasInProgressMessage && (
  <div className="chat-bubble assistant">
    <div className="typing-indicator">
      <span className="dot" /><span className="dot" /><span className="dot" />
    </div>
  </div>
)}
```

`hasInProgressMessage` = `messages.some(m => m.isStreaming)`. When the first `text_token` arrives and the streaming bubble is created, the typing indicator disappears naturally.

```css
.typing-indicator { display: flex; gap: 4px; align-items: center; height: 16px; }
.typing-indicator .dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--teal); opacity: 0.4;
  animation: typingBounce 1.2s ease-in-out infinite;
}
.typing-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-5px); opacity: 1; }
}
```

---

## 5. Phase 12B — Chat UX Improvements

### Destination Preview Card in Chat
When `clarification_questions` arrive and `pendingTrip.destination` is a known destination:
- Render a glassmorphic card ABOVE the clarification chips with:
  - Destination banner photo (from a frontend `DESTINATION_BANNERS` map mirroring `destination_images.py`)
  - Short tagline (static map, ~10 entries for popular destinations)
  - Inline `⚡ Generate now` button

### Active Preferences Strip (Freeform ↔ Guided)
```tsx
{inputMode === 'chat' && (guidedStyles.length > 0 || guidedDestination) && (
  <div className="guided-prefs-strip">
    <span className="prefs-summary">
      {guidedDestination && <span>📍 {guidedDestination}</span>}
      {guidedStyles.map(s => <span key={s}>{s}</span>)}
      <span>{guidedPace}</span>
    </span>
    <button className="btn-edit-prefs" onClick={() => setInputMode('guided')}>
      Edit in Builder ↗
    </button>
  </div>
)}
```

### Clarification Progress Counter
```tsx
<div className="clarification-progress">
  Question {questionIndex + 1} of {totalQuestions}
  <div className="progress-bar">
    <div className="progress-fill" style={{ width: `${((questionIndex+1)/totalQuestions)*100}%` }} />
  </div>
</div>
```

### Multi-Select Soft Cap Hint
```tsx
{selectedAnswers[q.id]?.length >= 4 && (
  <p className="multiselect-hint">
    💡 Tip: 2–3 styles give the most focused results
  </p>
)}
```

---

## 6. Phase 12C — Landing Page Polish

### Destination Card Sub-Labels (page.tsx only)
Add a `<p className="dest-card-sub">` under each destination card name:

| Destination | Sub-label |
|---|---|
| Goa | `Sun, sea, spice & Portuguese forts` |
| Rajasthan | `Royal forts, desert dunes & vibrant bazaars` |
| Lisbon | `Trams, tiled facades & Atlantic sunsets` |
| Kyoto | `Temple gardens, geishas & seasonal foliage` |

### Ken Burns Hero Carousel
CSS-only: 5 destination photos, `@keyframes kenBurns` scales image from 1 → 1.08 over 7s, crossfade on transition.

```css
@keyframes kenBurns {
  0% { transform: scale(1) translate(0, 0); }
  100% { transform: scale(1.08) translate(-2%, -1%); }
}
.hero-carousel-slide { animation: kenBurns 7s ease-in-out infinite alternate; }
```

---

## 7. Phase 12D — Token Usage Reduction

### Target Savings

| Location | Current | After | Saving |
|---|---|---|---|
| `CLARIFICATION_SYSTEM_PROMPT` | ~350 tokens | ~180 tokens | ~170 tokens/call |
| Niche scraper scoring | Up to 2,500 tokens | ~400 tokens (top-8) | ~2,100 tokens/call |
| Editor agent state (full itinerary) | ~1,200–2,000 tokens | ~200 tokens (patch only) | ~1,800 tokens/call |
| SSE event `description` truncation | Unlimited | 120 chars | Reduces JSON payload size |

### Strategy per Location

**`CLARIFICATION_SYSTEM_PROMPT`** — Remove:
- Repeated JSON schema examples
- Redundant `"Remember:"` footer lines
- Verbose option listing when a compact reference works

**Niche scraper** — Pre-sort by VADER compound score + mention count, keep top-8 before LLM call:
```python
candidates = sorted(candidates, key=lambda x: x.get("vader_compound", 0), reverse=True)[:8]
```

**Editor agent** — Pass only the day/stop being edited, not full itinerary JSON:
```python
patch_context = {
    "target_day": state["target_day"],
    "target_stop": next(s for s in day.stops if s.xid == state["target_stop_id"]),
    "destination": state["itinerary"].destination,
}
```

---

## 8. Phase 12E — Frontend Performance

### Identified Bottlenecks
1. `handleSend` recreated every render (no `useCallback`) — causes child prop churn.
2. `StopCard` re-renders on every chat message update because `ItineraryView` is a sibling in the same parent.
3. Aurora blobs may trigger layout recalculation without `will-change`.
4. Guided Builder destination text input triggers `pendingTrip` sync on every keystroke.

### Solutions

```typescript
// ChatPanel.tsx
const handleSend = useCallback(async (text, options) => { ... }, [
  messages, pendingTrip, activeClarification, guidedDestination, guidedDays, ...
]);
```

```typescript
// ItineraryView.tsx
const StopCard = React.memo(function StopCard({ stop, dayIndex, ... }) {
  ...
}, (prev, next) => prev.stop.xid === next.stop.xid && prev.dayIndex === next.dayIndex);
```

```css
/* globals.css */
.aurora-blob     { will-change: transform; }
.stop-card       { will-change: transform; }
.chat-hub-instant-bar { will-change: opacity, transform; }
```

```typescript
// Debounce destination input in Guided Builder
const debouncedSetDestination = useMemo(
  () => debounce((val: string) => handleGuidedDestinationChange(val), 300),
  []
);
```

---

## 9. Phase 12F — Backend Resilience

### "Did You Mean?" Fuzzy Match
```python
# places_tool.py
import difflib

KNOWN_DESTINATIONS = ["Goa", "Mumbai", "Delhi", "Jaipur", "Kolkata", "Bengaluru", 
                       "Hyderabad", "Chennai", "Rajasthan", "Manali", "Kashmir",
                       "Lisbon", "Paris", "Tokyo", "Bali", "Kyoto", "Rome", ...]

def fuzzy_match_destination(name: str) -> str | None:
    matches = difflib.get_close_matches(name.title(), KNOWN_DESTINATIONS, n=1, cutoff=0.75)
    return matches[0] if matches else None
```

If Nominatim returns `(0, 0)`, call `fuzzy_match_destination()` and emit a `destination_suggestion` SSE event. Frontend shows a `Did you mean [X]?` chip.

### Wikimedia URL Normalisation
```python
# In fetch_wikimedia_image:
photo_url = (
    d.get("originalimage", {}).get("source")
    or d.get("thumbnail", {}).get("source")
)
```

---

## 10. Verification Plan

| Step | Command | Expected |
|---|---|---|
| Frontend build | `npm run build` in `frontend/` | 0 TypeScript / Turbopack errors |
| Backend tests | `.venv\Scripts\python.exe -m pytest tests/` in `backend/` | 43/43 passing |
| Streaming test | Send any chat message | `...` indicator shows immediately, then words appear progressively |
| Token check | Google AI Studio usage logs for clarification calls | Noticeably fewer input tokens vs Phase 11 |
| Performance | Chrome DevTools Performance panel on ItineraryView | No unnecessary StopCard re-renders on chat updates |
