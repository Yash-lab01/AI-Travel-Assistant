"""
Tavily Search Tool — Phase 2
Fetches travel blog articles, community discussions, and off-the-beaten-path recommendations.
Uses Tavily Search API (free tier: 1000 queries/month) with rich snippet extraction.
"""
from __future__ import annotations
import os
import httpx
from typing import Optional

TAVILY_KEY = os.getenv("TAVILY_API_KEY", "")


async def search_tavily_travel_content(
    destination: str,
    query_type: str = "hidden_gems",
    max_results: int = 5,
) -> list[dict]:
    """
    Search for travel content regarding a destination using Tavily.
    
    Returns a list of dicts:
      [
        {
          "title": str,
          "url": str,
          "content": str,
          "source_type": "tavily_blog" | "reddit",
          "score": float
        }
      ]
    """
    if not TAVILY_KEY:
        return _get_mock_tavily_results(destination)

    # Build targeted queries
    if query_type == "reddit":
        query = f'site:reddit.com "{destination}" hidden gems recommendations locals'
    else:
        query = f'"{destination}" best hidden gems off the beaten path local secrets 2024 travel blog'

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_KEY,
                    "query": query,
                    "search_depth": "basic",
                    "include_answer": False,
                    "max_results": max_results,
                },
            )
            if resp.status_code != 200:
                return _get_mock_tavily_results(destination)

            data = resp.json()
            results = data.get("results", [])
            formatted = []

            for r in results:
                url = r.get("url", "")
                source_type = "reddit" if "reddit.com" in url else "tavily_blog"
                formatted.append({
                    "title": r.get("title", ""),
                    "url": url,
                    "content": r.get("content", ""),
                    "source_type": source_type,
                    "score": r.get("score", 0.8),
                })

            return formatted if formatted else _get_mock_tavily_results(destination)

    except Exception:
        return _get_mock_tavily_results(destination)


def _get_mock_tavily_results(destination: str) -> list[dict]:
    """Mock search results for popular and Indian destinations when offline or no key."""
    dest_lower = destination.lower()

    if "lisbon" in dest_lower:
        return [
            {
                "title": "Secret Lisbon: 10 Hidden Gems Locals Don't Want You to Miss",
                "url": "https://travelblog.example.com/lisbon-hidden-gems",
                "content": "Skip the crowded Santa Justa lift and head to Miradouro da Senhora do Monte for the most breathtaking sunset. Visit Jardim do Torel, a tranquil hillside oasis with sun loungers and a secret cafe. Don't miss Conserveira de Lisboa, an artisanal canned fish shop running since 1930.",
                "source_type": "tavily_blog",
                "score": 0.9,
            },
            {
                "title": "r/travel - My favorite non-touristy spots in Lisbon after living there for 2 years",
                "url": "https://www.reddit.com/r/travel/comments/lisbon_gems",
                "content": "Feira da Ladra flea market in Alfama on Tuesdays and Saturdays is iconic. Also check out Ler Devagar bookstore inside LX Factory and the quiet cloister of Convento do Carmo without the crazy lines.",
                "source_type": "reddit",
                "score": 0.88,
            },
        ]
    elif "rajasthan" in dest_lower or "jaipur" in dest_lower:
        return [
            {
                "title": "Offbeat Rajasthan: Hidden Stepwells and Secret Havelis",
                "url": "https://travelblog.example.com/rajasthan-secrets",
                "content": "Panna Meena ka Kund near Amer is an architectural marvel with geometric criss-cross staircases that most tour buses bypass. Visit Chand Baori and the serene Galta Ji Monkey Temple hidden between mountain cliffs.",
                "source_type": "tavily_blog",
                "score": 0.92,
            },
            {
                "title": "r/india - Hidden gems in Jaipur that tourists always miss",
                "url": "https://www.reddit.com/r/india/comments/jaipur_local_spots",
                "content": "Gaitore Ki Chhatriyan has incredible white marble cenotaphs with zero crowds. For food, try the street lassi at Lassiwala MI Road and sunset tea near Nahargarh fort edge.",
                "source_type": "reddit",
                "score": 0.87,
            },
        ]
    elif "goa" in dest_lower:
        return [
            {
                "title": "Secret South Goa: Unspoiled Beaches and Portuguese Quarters",
                "url": "https://travelblog.example.com/south-goa-gems",
                "content": "Fontainhas Latin Quarter in Panjim is full of colorful colonial mansions and heritage bakeries like Confeitaria 31 de Janeiro. For peace, visit Butterfly Beach and Cola Beach with its natural freshwater lagoon.",
                "source_type": "tavily_blog",
                "score": 0.91,
            },
        ]
    elif "kyoto" in dest_lower:
        return [
            {
                "title": "Kyoto Beyond the Crowds: Quiet Zen Gardens and Hidden Tea Houses",
                "url": "https://travelblog.example.com/kyoto-quiet",
                "content": "Instead of crowded Fushimi Inari, visit Otagi Nenbutsu-ji with 1,200 whimsical stone rakan sculptures in Arashiyama. Walk along the Philosopher's Path early morning and visit Honen-in temple's mossy gateway.",
                "source_type": "tavily_blog",
                "score": 0.93,
            },
        ]
    else:
        return [
            {
                "title": f"The Ultimate Insider Travel Guide to {destination}",
                "url": f"https://travelblog.example.com/{destination.lower().replace(' ', '-')}-secrets",
                "content": f"Discover the secret alleyway cafes, historic neighborhood courtyards, and local artisan markets in {destination} away from the main tourist strips.",
                "source_type": "tavily_blog",
                "score": 0.85,
            },
        ]
