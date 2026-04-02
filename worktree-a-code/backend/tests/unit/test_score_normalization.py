# Tests for AutoSCORE 4D score normalization and color mapping
# Sub-task 1: Fix scoring x100 bug
#
# The AutoSCORE 4D rubric uses 4 dimensions x 0-3 = total 0-12.
# The old code multiplied scores < 2 by 100, causing 1 -> 100 overflow.
# These tests verify the fix: scores stay in the 0-12 range.
"""
TDD RED phase: Tests for normalize_autoscore() and score_to_color().

These functions are extracted from agent_service.py score_nodes() to be
independently testable. The rubric is 0-12 (4 dims x 0-3 each).
"""

import pytest


class TestNormalizeAutoscore:
    """Tests that normalize_autoscore keeps scores in 0-12 range."""

    def test_score_of_1_not_multiplied_to_100(self):
        """A legitimate score of 1/12 must NOT become 100."""
        from app.services.scoring_utils import normalize_autoscore

        result = normalize_autoscore(1.0)
        assert result == 1.0, f"Score 1.0 should stay 1.0, got {result}"

    def test_score_of_0_stays_zero(self):
        """Score of 0 (all dimensions 0) stays 0."""
        from app.services.scoring_utils import normalize_autoscore

        result = normalize_autoscore(0.0)
        assert result == 0.0, f"Score 0.0 should stay 0.0, got {result}"

    def test_score_of_12_stays_12(self):
        """Perfect score of 12 stays 12."""
        from app.services.scoring_utils import normalize_autoscore

        result = normalize_autoscore(12.0)
        assert result == 12.0, f"Score 12.0 should stay 12.0, got {result}"

    def test_score_of_0_5_stays_0_5(self):
        """Fractional score in 0-12 range stays unchanged."""
        from app.services.scoring_utils import normalize_autoscore

        result = normalize_autoscore(0.5)
        assert result == 0.5, f"Score 0.5 should stay 0.5, got {result}"

    def test_max_output_never_exceeds_12(self):
        """No input in 0-12 range produces output > 12."""
        from app.services.scoring_utils import normalize_autoscore

        for score in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
            result = normalize_autoscore(float(score))
            assert result <= 12.0, (
                f"Score {score} normalized to {result}, exceeds 12"
            )

    def test_negative_score_clamped_to_zero(self):
        """Negative scores (invalid) are clamped to 0."""
        from app.services.scoring_utils import normalize_autoscore

        result = normalize_autoscore(-5.0)
        assert result == 0.0, f"Negative score should clamp to 0, got {result}"

    def test_score_above_12_clamped_to_12(self):
        """Scores above 12 (invalid) are clamped to 12."""
        from app.services.scoring_utils import normalize_autoscore

        result = normalize_autoscore(100.0)
        assert result == 12.0, f"Score 100 should clamp to 12, got {result}"

    @pytest.mark.parametrize(
        "raw_score,expected",
        [
            (0.0, 0.0),
            (1.0, 1.0),
            (1.5, 1.5),
            (3.0, 3.0),
            (6.0, 6.0),
            (9.0, 9.0),
            (12.0, 12.0),
        ],
    )
    def test_valid_scores_pass_through_unchanged(self, raw_score, expected):
        """Valid 0-12 scores pass through without modification."""
        from app.services.scoring_utils import normalize_autoscore

        result = normalize_autoscore(raw_score)
        assert result == expected, (
            f"Score {raw_score} should normalize to {expected}, got {result}"
        )


class TestScoreToColor:
    """Tests that score_to_color maps 0-12 scores to correct Obsidian colors.

    Color mapping on 0-12 scale (proportional to the old 0-100):
      >= 10 -> "2" (green, mastered)
      >= 7  -> "3" (purple, partial understanding)
      < 7   -> "4" (red, not understood)
    """

    def test_perfect_score_is_green(self):
        """12/12 -> green (color "2")."""
        from app.services.scoring_utils import score_to_color

        assert score_to_color(12.0) == "2"

    def test_score_10_is_green(self):
        """10/12 -> green (color "2")."""
        from app.services.scoring_utils import score_to_color

        assert score_to_color(10.0) == "2"

    def test_score_9_is_purple(self):
        """9/12 -> purple (color "3")."""
        from app.services.scoring_utils import score_to_color

        assert score_to_color(9.0) == "3"

    def test_score_7_is_purple(self):
        """7/12 -> purple (color "3")."""
        from app.services.scoring_utils import score_to_color

        assert score_to_color(7.0) == "3"

    def test_score_6_is_red(self):
        """6/12 -> red (color "4")."""
        from app.services.scoring_utils import score_to_color

        assert score_to_color(6.0) == "4"

    def test_score_0_is_red(self):
        """0/12 -> red (color "4")."""
        from app.services.scoring_utils import score_to_color

        assert score_to_color(0.0) == "4"

    def test_score_1_is_red_not_green(self):
        """1/12 must be red, NOT green (old bug: 1*100=100 -> green)."""
        from app.services.scoring_utils import score_to_color

        color = score_to_color(1.0)
        assert color == "4", (
            f"Score 1/12 should be red ('4'), got '{color}'. "
            "This was the x100 bug: 1 became 100 -> green."
        )

    @pytest.mark.parametrize(
        "score,expected_color",
        [
            (0.0, "4"),   # red
            (3.0, "4"),   # red
            (6.0, "4"),   # red (just below threshold)
            (6.9, "4"),   # red
            (7.0, "3"),   # purple (threshold)
            (8.0, "3"),   # purple
            (9.0, "3"),   # purple
            (9.9, "3"),   # purple (just below green)
            (10.0, "2"),  # green (threshold)
            (11.0, "2"),  # green
            (12.0, "2"),  # green (max)
        ],
    )
    def test_color_boundaries(self, score, expected_color):
        """Verify color mapping at all boundary points."""
        from app.services.scoring_utils import score_to_color

        result = score_to_color(score)
        assert result == expected_color, (
            f"Score {score} -> expected color '{expected_color}', got '{result}'"
        )


class TestAutoscoreToPercent:
    """Tests for autoscore_to_percent: converts 0-12 to 0-100 for FSRS."""

    def test_zero_maps_to_zero(self):
        from app.services.scoring_utils import autoscore_to_percent

        assert autoscore_to_percent(0.0) == 0.0

    def test_twelve_maps_to_100(self):
        from app.services.scoring_utils import autoscore_to_percent

        assert autoscore_to_percent(12.0) == 100.0

    def test_six_maps_to_50(self):
        from app.services.scoring_utils import autoscore_to_percent

        assert autoscore_to_percent(6.0) == 50.0

    def test_score_1_maps_to_about_8(self):
        """Score 1/12 should become ~8.33, NOT 100."""
        from app.services.scoring_utils import autoscore_to_percent

        result = autoscore_to_percent(1.0)
        assert result < 10.0, (
            f"Score 1/12 -> {result}%, should be ~8.33 not 100"
        )
        assert abs(result - 8.33) < 0.1

    def test_clamps_negative(self):
        from app.services.scoring_utils import autoscore_to_percent

        assert autoscore_to_percent(-5.0) == 0.0

    def test_clamps_over_12(self):
        from app.services.scoring_utils import autoscore_to_percent

        assert autoscore_to_percent(100.0) == 100.0
