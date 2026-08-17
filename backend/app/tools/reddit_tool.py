"""
Reddit Public Discussion Scraper Tool — Phase 2
Extracts authentic community recommendations, hidden gems, and local tips from public Reddit threads.
Uses Reddit's public JSON API (zero authentication / zero keys required) with custom User-Agent.
"""
from __future__ import annotations
import httpx
from typing import Optional

REDDIT_USER_AGENT = "WanderAI/0.1 (TravelAssistantBot by /u/travel_dev)"


async def search_reddit_travel_discussions(
    destination: str,
    subreddits: list[str] | None = None,
    limit: int = 5,
) -> list[dict]:
    """
    Search Reddit for travel discussions and hidden gems in a given destination.

    Returns a list of dicts:
      [
        {
          "title": str,
          "content": str,
          "subreddit": str,
          "score": int,
          "url": str,
          "source_type": "reddit"
        }
      ]
    """
    if subreddits is None:
        subreddits = ["travel", "solotravel", "Shoestring"]

    results: list[dict] = []
    clean_dest = destination.split(",")[0].strip()

    headers = {
        "User-Agent": REDDIT_USER_AGENT,
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=8.0, headers=headers, follow_redirects=True) as client:
        for sub in subreddits:
            url = f"https://www.reddit.com/r/{sub}/search.json"
            params = {
                "q": f'"{clean_dest}" hidden gems OR secret OR local OR underrated',
                "restrict_sr": "1",
                "sort": "relevance",
                "limit": limit,
            }
            try:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        post = child.get("data", {})
                        title = post.get("title", "")
                        selftext = post.get("selftext", "")
                        score = post.get("score", 0)
                        permalink = post.get("permalink", "")

                        if title or selftext:
                            snippet = f"{title}. {selftext[:400]}"
                            results.append({
                                "title": title,
                                "content": snippet,
                                "subreddit": sub,
                                "score": score,
                                "url": f"https://www.reddit.com{permalink}",
                                "source_type": "reddit",
                            })
            except Exception:
                continue

    return results
