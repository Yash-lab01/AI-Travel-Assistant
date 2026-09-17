# Phase 11: Dual-Mode Intake & Multi-Select Planning Studio

> **Status**: COMPLETED ✅  
> **Date**: September 2026  
> **Author**: Antigravity AI Engineering & UX Architecture  

---

## 1. Problem Statement & Motivation

During user testing and travel planning workflows, the current conversational chat intake exhibited several friction points:
1. **Limited Information Gathering**: The previous chat intake only asked 1–2 brief questions, missing critical dimensions such as travel companions, specific activities, and budget tiers.
2. **Lack of Multi-Select**: Travel preferences are rarely mutually exclusive. A traveler often wants **both** authentic hidden gems *and* iconic landmarks, or **both** street food trails *and* historical forts. Restricting clarification chips to single-select forced artificial trade-offs.
3. **Modal Rigidity**: Some users prefer a quick conversational chat, while others prefer a visual, structured form where they can toggle all options at a glance without having to type back and forth.
4. **Questionnaire Fatigue**: When users just want an immediate itinerary for a known destination, being forced to answer clarifying questions before generation begins slows them down. There was no instant escape hatch to "just generate with sensible defaults".

Phase 11 solves these challenges by introducing a **dual-mode planning studio** with rich multi-select capabilities, strategic slot-filling, and an instant generation escape hatch.

---

## 2. Core Architecture & Feature Pillars

```
                     ┌─────────────────────────────────────────────────┐
                     │          WanderAI Planning Studio Header        │
                     └────────────────────────┬────────────────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
      ┌───────────────────────────────┐               ┌───────────────────────────────┐
      │      💬 Freeform Chat         │               │      ✨ Guided Builder        │
      ├───────────────────────────────┤               ├───────────────────────────────┤
      │ • Conversational natural input│               │ • Visual destination selector │
      │ • Strategic slot-filling LLM  │               │ • Visual duration day pills   │
      │ • Multi-select chips (✓)      │               │ • Multi-select style & vibe   │
      │ • "⚡ Generate with info"      │               │ • Pacing, budget & companions │
      │ • Real-time agent event feed  │               │ • Must-have activity pills    │
      └───────────────┬───────────────┘               │ • Live summary preview strip  │
                      │                               └───────────────┬───────────────┘
                      │                                               │
                      └───────────────────────┬───────────────────────┘
                                              │
                                              ▼
                             ┌─────────────────────────────────┐
                             │       Shared Request State      │
                             │  {destination, days, styles,    │
                             │   interests, pace, dietary...}  │
                             └────────────────┬────────────────┘
                                              │
                                              ▼
                             ┌─────────────────────────────────┐
                             │    Intake Agent & LangGraph     │
                             │   (List parsing & auto-fill)    │
                             └─────────────────────────────────┘
```

---

## 3. Detailed Component Specifications

### Pillar 1: Top Mode Segmented Controller
- Located immediately below the chat header in `ChatPanel.tsx`.
- Two distinct modes:
  - `💬 Freeform Chat`: Conversational interaction with assistant reasoning.
  - `✨ Guided Builder`: Visual configuration matrix.
- **State Synchronization**: Any destination or parameters set in one mode are seamlessly mirrored to the other.

### Pillar 2: Visual Guided Builder Matrix
When in Guided Builder mode, the interface displays clean, categorized preference blocks:

1. **Destination & Quick Picks**:
   - Freeform search/text input.
   - 1-click popular destination pills: `Goa`, `Mumbai`, `Rajasthan`, `Lisbon`, `Kyoto`, `Kashmir`, `Paris`.
2. **Duration (Days)**:
   - Visual duration pills: `1 Day`, `2 Days`, `3 Days`, `4 Days`, `5 Days`, `7 Days`, `10 Days`.
3. **Travel Style & Vibe (Multi-Select)**:
   - `🏛️ Iconic Landmarks`, `💎 Hidden Gems`, `🏰 Cultural Heritage`, `🍲 Foodie & Markets`, `🌿 Scenic Nature`, `🏄 Adventure`, `🧘 Relaxed Leisure`.
4. **Daily Sightseeing Pace**:
   - `🧘 Relaxed (2-3 stops/day)`, `⚡ Moderate (4-5 stops/day)`, `🏃 Packed (6+ stops/day)`.
5. **Budget Tier & Travel Companions**:
   - Budget: `🪙 Budget / Backpacker`, `⚖️ Mid-Range`, `✨ Luxury / Premium`.
   - Companions: `🎒 Solo Explorer`, `💑 Couple`, `👨‍👩‍👧 Family with Kids`, `👥 Friends Group`.
6. **Must-Have Experiences & Interests (Multi-Select)**:
   - `📸 Viewpoints & Photo Spots`, `☕ Artisanal Cafes`, `🏖️ Beaches & Coast`, `🛍️ Bazaars & Flea Markets`, `🌄 Sunset Points`, `🎨 Art & Museums`, `🍜 Local Street Food Trails`.
7. **Dietary Preferences (Multi-Select)**:
   - `🌱 Vegan`, `🥗 Vegetarian`, `🕌 Halal`, `🌾 Gluten-Free`, `🕊️ Jain`.
8. **Summary & Action Bar**:
   - Real-time readable summary (e.g. `📍 Kyoto · 4 Days · 💎 Hidden Gems + 🍲 Foodie · 🧘 Relaxed`).
   - `🚀 Generate Custom Itinerary` (disabled only if destination is empty).
   - `↺ Reset Options` to restore default balanced settings.

### Pillar 3: Multi-Select Clarification Engine
- **Schema Update**:
  - `ClarificationQuestion` receives `is_multi_select: bool = False`.
  - Categories like `travel_style`, `interests`, `activity`, and `dietary` have `is_multi_select = True`.
- **Frontend State**:
  - `selectedAnswers` updated from `Record<string, string>` to `Record<string, string[]>`.
  - Toggling an option adds/removes it from the array.
  - Active visual styling: luminous teal glow, checkmark icon `✓`, and distinct border.
- **Backend Ingestion**:
  - `ChatRequest.answers` accepts `Optional[dict[str, Any]]` (both strings and lists of strings).
  - `intake_agent.py` merges list answers into `TripRequest.interests`, blends `travel_style`, and tunes `niche_weight`.

### Pillar 4: Strategic Fixed-Info Retrieval in Freeform Chat
- When a user chats in Freeform mode, `intake_agent.py` evaluates the 5 core dimensions:
  1. **Destination** (essential)
  2. **Duration** (essential)
  3. **Travel Style / Vibe** (essential for personalization)
  4. **Pacing** (valuable refinement)
  5. **Companions / Budget** (valuable refinement)
- If one or more core dimensions are missing from an informal prompt (e.g. *"Trip to Rome"* or *"Kashmir with college friends"*), the agent responds conversationally and generates targeted, multi-select questions specifically addressing the missing dimensions.

### Pillar 5: Instant "⚡ Generate Trip with Given Info" Action
- **No Roadblocks**: If a traveler doesn't wish to answer multiple questions, they can click `⚡ Generate Trip with Given Info (Defaults)`.
- Available both inside the clarification message bubble AND as a persistent action chip above the chat input bar whenever a destination has been detected.
- Directly invokes the planning pipeline with `force_plan: true`, applying sensible defaults for any unselected parameters.

---

## 4. Modified Files & Technical Blueprint

| Layer | File | Planned Modifications |
|---|---|---|
| **Backend Schemas** | `backend/app/models/schemas.py` | Add `is_multi_select: bool = False` to `ClarificationQuestion`; expand `ChatRequest.answers` to `dict[str, Any]`. |
| **Backend Agents** | `backend/app/agents/intake_agent.py` | Strategic missing dimension detection; multi-select list parsing for `answers`; expanded `DESTINATION_QUESTIONS`. |
| **Frontend Types** | `frontend/src/types/index.ts` | Mirror `is_multi_select` in `ClarificationQuestion`; update `ChatMessage` & clarification types. |
| **Frontend UI** | `frontend/src/components/ChatPanel.tsx` | Top mode switcher; Guided Builder visual matrix; multi-select chip toggle state; instant generate actions. |
| **Frontend Styling** | `frontend/src/app/globals.css` | Segmented control styles; guided builder responsive layout; multi-select chip active states (`✓`). |

---

## 5. Verification & Test Plan

1. **Backend Unit Tests**:
   - Verify multi-select answer lists correctly map to `TripRequest` fields.
   - Verify `force_plan` bypasses all clarification questions.
   - **Status**: 43/43 pytest tests passing ✅
2. **Frontend Build & Type Safety**:
   - `npm run build` in Next.js 16 to confirm 0 TypeScript or Turbopack errors.
3. **End-to-End User Verification**:
   - Test mode switching between Chat and Guided Builder.
   - Test multi-selection of 3+ interests and verify they flow into the final itinerary.
   - Test "⚡ Generate Trip with Given Info" on partial prompts.
