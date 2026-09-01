"""
Local Ollama Narration Client — Phase 5
Communicates with a locally running Ollama instance (default: http://localhost:11434)
to generate zero-latency, evocative 1-2 sentence stop narrations using fine-tuned LoRA models
(e.g., `travel-narrator` or `llama3.2:3b`).

Gracefully falls back if Ollama is not running locally.
"""
from __future__ import annotations
import httpx
import os
import re
import json
import asyncio
from typing import Optional, Any

from app.models.schemas import Stop

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
PREFERRED_MODELS = [
    "travel-narrator",
    "travel-narrator:latest",
    "llama3.2:3b",
    "llama3.2",
    "llama3.1:8b",
    "llama3.1",
    "mistral",
]

SYSTEM_PROMPT = (
    "You are an expert travel writer specializing in evocative, atmospheric, "
    "and sensory travel narrations for day-by-day itineraries. "
    "Write exactly 1-2 sensory, evocative sentences (under 30 words). "
    "Avoid generic tourist clichés like 'must-see' or 'rich history'. Use present tense."
)


async def get_available_ollama_model(client: Optional[httpx.AsyncClient] = None) -> Optional[str]:
    """
    Check if local Ollama is active and return the best available travel narration model.
    Returns None if Ollama is unreachable.
    """
    close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=1.5)
        close_client = True

    try:
        resp = await client.get(f"{OLLAMA_HOST}/api/tags")
        if resp.status_code == 200:
            data = resp.json()
            installed_models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
            installed_full = [m.get("name", "") for m in data.get("models", [])]

            for pref in PREFERRED_MODELS:
                if pref in installed_full or pref.split(":")[0] in installed_models:
                    return pref
            # If any other model is installed, use the first one
            if installed_full:
                return installed_full[0]
    except Exception:
        pass
    finally:
        if close_client:
            await client.aclose()

    return None


async def is_ollama_available() -> bool:
    """Return True if Ollama is running and has at least one model."""
    model = await get_available_ollama_model()
    return model is not None


async def generate_stop_narration(
    place_name: str,
    category: str,
    destination: str,
    context: str = "",
    model: Optional[str] = None,
) -> Optional[str]:
    """
    Generate an evocative 1-2 sentence stop narration via local Ollama.
    Returns None if Ollama is unreachable or generation fails.
    """
    if not place_name or len(place_name.strip()) < 2:
        return None

    clean_name = place_name.split("(")[0].strip()
    
    async with httpx.AsyncClient(timeout=8.0) as client:
        selected_model = model or await get_available_ollama_model(client)
        if not selected_model:
            return None

        prompt = (
            f"Write a 1-2 sentence evocative, atmospheric travel narration for {clean_name}, "
            f"a {category} in {destination}."
        )
        if context and len(context.strip()) > 5:
            prompt += f"\nContext & Atmosphere: {context.strip()}"

        try:
            resp = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": selected_model,
                    "prompt": prompt,
                    "system": SYSTEM_PROMPT,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "top_p": 0.9,
                        "num_predict": 60,
                        "repeat_penalty": 1.15,
                    },
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data.get("response", "").strip(' \n"')
                # Clean up quotes and newlines
                cleaned = re.sub(r'\s+', ' ', raw_text).strip()
                if cleaned and len(cleaned) > 15:
                    return cleaned
        except Exception as e:
            print(f"[ollama_narrator] Local generation failed: {e}")

    return None


async def generate_stop_narrations_batch(
    stops: list[Stop],
    destination: str,
    model: Optional[str] = None,
) -> list[Optional[str]]:
    """
    Concurrently generate narrations for a batch of stops using local Ollama.
    Returns a list of narrations matching stops length (with None for any failure).
    """
    if not stops:
        return []

    async with httpx.AsyncClient(timeout=10.0) as client:
        selected_model = model or await get_available_ollama_model(client)
        if not selected_model:
            return [None] * len(stops)

        tasks = [
            generate_stop_narration(
                place_name=s.name,
                category=s.category or "attraction",
                destination=destination,
                context=s.description or "",
                model=selected_model,
            )
            for s in stops
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        narrations: list[Optional[str]] = []
        for res in results:
            if isinstance(res, str) and res:
                narrations.append(res)
            else:
                narrations.append(None)

        return narrations
