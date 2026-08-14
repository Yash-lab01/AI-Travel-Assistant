"""
Hidden Gem Scoring Engine
Formula (Phase 2 — stub with formula defined):

    hidden_gem_score = (
        niche_mention_count × sentiment_weight
      + source_diversity_bonus
      - popularity_penalty
    ) / normalization_factor

Where:
  - sentiment_weight   = avg VADER compound score of all mention contexts (-1 to 1)
  - source_diversity_bonus = 0.2 if ≥2 distinct source types (Reddit + blog/Tavily)
  - popularity_penalty = log(review_count + 1) / log(max_review_count + 1)  [log-normalised]
  - normalization_factor = clamps result to [0, 1]

This formula is intentionally simple and explainable:
  - log-normalization prevents a place with 50k reviews vs 10k reviews looking equally "popular"
  - source diversity bonus rewards cross-platform mentions (harder to game)
  - sentiment_weight means vague mentions count for less than enthusiastic ones
"""
import math
from app.models.schemas import NicheScore


def compute_hidden_gem_score(
    mention_count: int,
    avg_sentiment: float,           # -1.0 to 1.0 (VADER compound)
    source_types: list[str],        # e.g. ["reddit", "tavily_blog"]
    google_review_count: int | None,
    max_review_count_in_batch: int = 10_000,
) -> float:
    """
    Returns a hidden_gem_score in [0, 1].
    Higher = more of a hidden gem (niche signal strong, popularity low).

    Formula breakdown:
      niche_signal      = scaled mentions (0-1) × sentiment factor (0-1)  [0..1]
      diversity_bonus   = +0.15 if mentioned across 2+ source types       [0..0.15]
      popularity_penalty= log-normalized review count × 0.4 weight        [0..0.4]
      raw = niche_signal + diversity_bonus - popularity_penalty, clamped to [0,1]

    Weights chosen so:
      - A perfect hidden gem (20 mentions, +1 sentiment, 2 sources, 0 reviews) → ~1.0
      - A pure tourist trap (1 mention, low sentiment, 1 source, 10k reviews) → ~0.05
      - A mid-tier niche spot (10 mentions, 0.6 sentiment, 2 sources, 500 reviews) → ~0.5
    """
    # ── Niche signal (max 1.0) ────────────────────────────────────────────────
    # Scale mention count (cap at 20 to avoid runaway scores)
    scaled_mentions = min(mention_count, 20) / 20.0

    # Sentiment weight: shift -1..1 → 0..1
    sentiment_factor = (avg_sentiment + 1.0) / 2.0
    niche_signal = scaled_mentions * sentiment_factor  # 0..1

    # ── Source diversity bonus (max 0.15) ─────────────────────────────────────
    unique_sources = len(set(source_types))
    diversity_bonus = 0.15 if unique_sources >= 2 else 0.0

    # ── Popularity penalty (max 0.4, log-normalised) ──────────────────────────
    # log-normalised so 10k vs 50k reviews doesn't look the same
    review_count = google_review_count or 0
    if max_review_count_in_batch <= 0:
        max_review_count_in_batch = 10_000

    log_norm = math.log(review_count + 1) / math.log(max_review_count_in_batch + 1)
    popularity_penalty = log_norm * 0.4  # weight: penalty can reduce score by at most 0.4

    # ── Combine and clamp ─────────────────────────────────────────────────────
    raw_score = niche_signal + diversity_bonus - popularity_penalty
    return round(max(0.0, min(1.0, raw_score)), 4)


def score_niche_spot(
    spot: NicheScore,
    max_review_count_in_batch: int = 10_000,
) -> NicheScore:
    """Compute and attach hidden_gem_score to a NicheScore object."""
    spot.hidden_gem_score = compute_hidden_gem_score(
        mention_count=spot.mention_count,
        avg_sentiment=spot.avg_sentiment,
        source_types=spot.sources,
        google_review_count=spot.google_review_count,
        max_review_count_in_batch=max_review_count_in_batch,
    )
    return spot
