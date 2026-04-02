# Tests for AutoSCORE 4D score normalization (0-12 -> 0-100)
# Sub-task 1: The x100 bug turns a raw score of 1 into 100.
# Correct behavior: 0-12 AutoSCORE scale should normalize to 0-100 via (score/12)*100.
"""
TDD Red-Green tests for score normalization logic in agent_service.py.

The AutoSCORE 4D rubric produces scores in 0-12 range (4 dims x 0-3 each).
Downstream consumers (color mapping, FSRS get_rating_from_score) expect 0-100.
The normalization function must convert correctly without overflow.
"""

import pytest

from app.services.agent_service import normalize_autoscore_to_100


class TestNormalizeAutoscoreTo100:
    """Verify AutoSCORE 0-12 -> 0-100 normalization."""

    def test_perfect_score_12_becomes_100(self):
        """A perfect 12/12 should normalize to 100."""
        assert normalize_autoscore_to_100(12) == 100.0

    def test_zero_score_stays_zero(self):
        """A score of 0 stays 0."""
        assert normalize_autoscore_to_100(0) == 0.0

    def test_score_1_does_not_become_100(self):
        """This is the exact bug: score=1 was being multiplied by 100.
        Correct: 1/12*100 = 8.33, NOT 100."""
        result = normalize_autoscore_to_100(1)
        assert result < 20, f"Score 1/12 should be ~8.33, got {result}"
        assert abs(result - 8.33) < 0.1

    def test_score_6_becomes_50(self):
        """Mid-range: 6/12 = 50."""
        assert abs(normalize_autoscore_to_100(6) - 50.0) < 0.1

    def test_score_9_becomes_75(self):
        """9/12 = 75."""
        assert abs(normalize_autoscore_to_100(9) - 75.0) < 0.1

    def test_score_10_becomes_about_83(self):
        """10/12 ~ 83.33 -> green threshold (>=80)."""
        result = normalize_autoscore_to_100(10)
        assert result >= 80, f"10/12 should map to green (>=80), got {result}"

    def test_score_7_becomes_about_58(self):
        """7/12 ~ 58.33 -> red zone (<60)."""
        result = normalize_autoscore_to_100(7)
        assert result < 60, f"7/12 should be in red zone (<60), got {result}"

    def test_float_score_0_85_treated_as_normalized_float(self):
        """If LLM returns 0.85 (a 0-1 float), convert to 85."""
        result = normalize_autoscore_to_100(0.85)
        assert abs(result - 85.0) < 0.1

    def test_already_in_100_scale_not_double_converted(self):
        """If score is already >12 (e.g. 75), it's already on 0-100 scale."""
        result = normalize_autoscore_to_100(75)
        assert abs(result - 75.0) < 0.1

    def test_negative_score_clamped_to_zero(self):
        """Negative scores should clamp to 0."""
        assert normalize_autoscore_to_100(-1) == 0.0

    def test_over_100_clamped(self):
        """Scores over 100 should clamp to 100."""
        assert normalize_autoscore_to_100(150) == 100.0
