"""
Unit tests for the hidden gem scoring formula.
Run with: pytest backend/tests/test_scoring.py -v

Phase 2 exit criteria: scoring produces defensible rankings on 3 known destinations.
"""
import pytest
from app.scoring.hidden_gem_score import compute_hidden_gem_score


class TestHiddenGemScore:

    def test_perfect_hidden_gem(self):
        """High mentions, positive sentiment, multiple sources, almost no reviews → near 1.0"""
        score = compute_hidden_gem_score(
            mention_count=15,
            avg_sentiment=0.8,
            source_types=["reddit", "tavily_blog"],
            google_review_count=50,
            max_review_count_in_batch=10_000,
        )
        assert score > 0.45, f"Expected high score for true hidden gem, got {score}"

    def test_popular_tourist_trap(self):
        """Low niche mentions, neutral sentiment, single source, massive review count → near 0"""
        score = compute_hidden_gem_score(
            mention_count=1,
            avg_sentiment=0.1,
            source_types=["reddit"],
            google_review_count=9_000,
            max_review_count_in_batch=10_000,
        )
        assert score < 0.15, f"Expected low score for popular tourist trap, got {score}"

    def test_diversity_bonus_applied(self):
        """Two source types should score higher than one, all else equal (no reviews to zero both out)."""
        score_single = compute_hidden_gem_score(
            mention_count=8, avg_sentiment=0.5,
            source_types=["reddit"],
            google_review_count=0, max_review_count_in_batch=10_000,
        )
        score_multi = compute_hidden_gem_score(
            mention_count=8, avg_sentiment=0.5,
            source_types=["reddit", "tavily_blog"],
            google_review_count=0, max_review_count_in_batch=10_000,
        )
        assert score_multi > score_single, f"Multi-source ({score_multi}) should score higher than single ({score_single})"

    def test_negative_sentiment_lowers_score(self):
        """Negative sentiment should reduce the score (use low reviews so penalty doesn't zero both)."""
        score_pos = compute_hidden_gem_score(
            mention_count=10, avg_sentiment=0.7,
            source_types=["reddit"], google_review_count=0, max_review_count_in_batch=10_000,
        )
        score_neg = compute_hidden_gem_score(
            mention_count=10, avg_sentiment=-0.5,
            source_types=["reddit"], google_review_count=0, max_review_count_in_batch=10_000,
        )
        assert score_pos > score_neg, f"Positive sentiment ({score_pos}) should score higher than negative ({score_neg})"

    def test_score_always_in_range(self):
        """Score must always be in [0, 1]."""
        for mention_count in [0, 1, 5, 20]:
            for sentiment in [-1.0, 0.0, 1.0]:
                for reviews in [0, 100, 5000, 50000]:
                    score = compute_hidden_gem_score(
                        mention_count=mention_count,
                        avg_sentiment=sentiment,
                        source_types=["reddit"],
                        google_review_count=reviews,
                        max_review_count_in_batch=50_000,
                    )
                    assert 0.0 <= score <= 1.0, f"Score {score} out of range"

    def test_zero_reviews_no_crash(self):
        """Spots not in Google Places (no reviews) should not crash."""
        score = compute_hidden_gem_score(
            mention_count=8, avg_sentiment=0.6,
            source_types=["reddit", "tavily_blog"],
            google_review_count=None,
            max_review_count_in_batch=10_000,
        )
        assert 0.0 <= score <= 1.0

    # ── Sanity check: known destinations ────────────────────────────────────
    def test_lisbon_alfama_backstreet_vs_belem_tower(self):
        """
        Alfama backstreet café (niche) should score higher than Belém Tower (tourist magnet).
        Representative of Lisbon destination sanity check.
        """
        alfama_cafe = compute_hidden_gem_score(
            mention_count=12, avg_sentiment=0.75,
            source_types=["reddit", "tavily_blog"],
            google_review_count=180,
            max_review_count_in_batch=15_000,
        )
        belem_tower = compute_hidden_gem_score(
            mention_count=2, avg_sentiment=0.3,
            source_types=["reddit"],
            google_review_count=14_000,
            max_review_count_in_batch=15_000,
        )
        assert alfama_cafe > belem_tower, (
            f"Alfama café ({alfama_cafe}) should outscore Belém Tower ({belem_tower})"
        )
