# Troubleshooting, Mistakes & Lessons Learned

This document serves as a persistent record of bugs encountered, root causes diagnosed, failed attempts, and concrete rules on **what NOT to do** in the WanderAI codebase.

---

## 1. LLM Response Formatting: `'list' object has no attribute 'strip'`
- **Symptom**:
  `AttributeError: 'list' object has no attribute 'strip'` thrown in `intake_agent.py`, `planner_agent.py`, and `niche_scraper.py`.
- **Root Cause**:
  Under recent versions of `langchain_google_genai` and `google-genai`, `response.content` is returned as a **list of content blocks** (e.g. `[{'type': 'text', 'text': '...', 'extras': {...}}]`) instead of a raw Python `str`. Calling `response.content.strip()` threw an unhandled exception and broke theme/narration generation, falling back to static default strings.
- **Rule / What to Do**:
  Always use `safe_extract_text(response.content)` across all agents:
  ```python
  def safe_extract_text(content: Any) -> str:
      if isinstance(content, str):
          return content.strip()
      if isinstance(content, list):
          parts = []
          for p in content:
              if isinstance(p, dict):
                  parts.append(p.get("text", ""))
              elif hasattr(p, "text"):
                  parts.append(getattr(p, "text", ""))
              else:
                  parts.append(str(p))
          return "".join(parts).strip()
      return str(content).strip()
  ```
- **What NOT to do**:
  ❌ Never call `response.content.strip()` directly on any LangChain invocation.

---

## 2. OpenTripMap JSON Format & Silent Fallback to Mock Data
- **Symptom**:
  Itineraries for Indian cities (Pune, Mumbai) or smaller destinations were returning generic fallback strings like *"Scenic Waterfront Promenade"*, *"Historic Old Town Center"*, and *"National Heritage Museum"*.
- **Root Cause**:
  In `places_tool.py`, the OpenTripMap API was called with `format=json`. The parser looked for GeoJSON attributes `f["properties"]["xid"]` and `f["geometry"]["coordinates"]`. But OpenTripMap with `format=json` returns flat dicts:
  `{"xid": "N...", "name": "...", "point": {"lat": ..., "lon": ...}}`.
  Because `properties` was `None`, all real attractions were skipped, resulting in an empty array `[]` and silently triggering `_mock_otm_places(lat, lon)`.
- **Rule / What to Do**:
  Support both flat JSON and GeoJSON shapes:
  ```python
  xid = f.get("xid") or f.get("properties", {}).get("xid")
  name = f.get("name") or f.get("properties", {}).get("name", "")
  point = f.get("point", {})
  lat = point.get("lat") or f.get("geometry", {}).get("coordinates", [None, None])[1]
  lon = point.get("lon") or f.get("geometry", {}).get("coordinates", [None, None])[0]
  ```
- **What NOT to do**:
  ❌ Never assume a 3rd-party geo API returns GeoJSON unless explicitly verified.
  ❌ Never mix mock POIs into real attraction lists when querying multi-zone subzones.

---

## 3. Provider Model Deprecations & 404s
- **Symptom**:
  - `Error calling model 'gemini-2.5-flash' (NOT_FOUND): 404 NOT_FOUND`
  - `The model llama-3.1-8b-instant does not exist or you do not have access to it`
- **Root Cause**:
  `gemini-2.5-flash` and `llama-3.1-8b-instant` were sunset or deprecated on Google AI Studio / Groq API endpoints.
- **Rule / Active Working Models**:
  - **Google AI Studio (Gemini)**: Use `gemini-3.5-flash` or `gemini-3.6-flash`.
  - **Groq**: Use `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, or `qwen/qwen3.6-27b`.
- **What NOT to do**:
  ❌ Do not reference legacy `gemini-2.5-flash` or `llama-3.1-8b-instant`.

---

## 4. Multi-Turn Destination Loss ("Unknown City")
- **Symptom**:
  User typed *"3 days in Mumbai"*, selected clarification preferences, and the final itinerary was titled *"3-Day Journey to Unknown"*.
- **Root Cause**:
  When submitting clarification chips, `handleSend` sent `"Submit preferences"`. The intake agent parsed that text independently and saw no city name, overriding `destination` with `"Unknown"`.
- **Rule / What to Do**:
  1. Frontend stores `pendingTrip: { destination, num_days }` and formats the submit message with the original destination.
  2. Frontend sends explicit `destination` and `num_days` in the JSON POST body.
  3. Backend graph state retains `state.get("destination")` and never overwrites it with `"Unknown"`.

---

## 5. Frontend Day Switching & Map Marker Errors
- **Symptom**:
  Clicking Day 2 or Day 3 tabs threw runtime exceptions or blank screens.
- **Root Cause**:
  If the backend returned fewer clusters than expected, or if `activeDay` was out of bounds, `days[activeDay]` became `undefined`. Accessing `currentDay.stops` threw `TypeError: Cannot read properties of undefined`.
  Additionally, passing invalid lat/lon or calling `fitBounds` on empty coordinate sets threw Leaflet errors.
- **Rule / What to Do**:
  1. Backend `_kmeans_cluster` strictly guarantees returning **EXACTLY `k` non-empty clusters** (`len(clusters) == k == num_days`).
  2. Frontend uses safe indexing:
     ```typescript
     const validActiveDay = (activeDay >= 0 && activeDay < days.length) ? activeDay : (activeDay === -1 ? -1 : 0);
     ```
  3. `MapView.tsx` validates coordinates (`typeof lat === 'number' && !isNaN(lat)`) and checks `bounds.isValid()` before calling `map.fitBounds()`.

---

## 6. LangSmith 403 Forbidden Console Spam
- **Symptom**:
  Constant terminal error logs: `Failed to POST https://api.smith.langchain.com/runs/multipart in LangSmith API: 403 Forbidden`.
- **Root Cause**:
  `LANGCHAIN_TRACING_V2=true` was enabled without a valid LangSmith API key.
- **Rule / What to Do**:
  Keep `LANGCHAIN_TRACING_V2=false` in `.env` unless actively debugging with a configured LangSmith workspace key.
