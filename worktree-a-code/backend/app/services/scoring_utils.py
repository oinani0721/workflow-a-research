# Canvas Learning System - Scoring Utilities
# Extracted from agent_service.py score_nodes() for testability.
#
# AutoSCORE 4D rubric: 4 dimensions x 0-3 = total 0-12.
# Previously the code multiplied scores < 2 by 100, causing 1 -> 100 overflow.
"""
Scoring normalization and color mapping utilities.

normalize_autoscore(): Clamp raw AutoSCORE total to valid 0-12 range.
score_to_color(): Map 0-12 score to Obsidian Canvas node color code.
"""


def normalize_autoscore(raw_score: float) -> float:
    """Normalize an AutoSCORE 4D total score to the 0-12 range.

    The AutoSCORE rubric has 4 dimensions scored 0-3 each, giving a
    total range of 0-12. This function clamps invalid values and
    passes valid scores through unchanged.

    No multiplication is applied -- the old x100 bug is removed.

    Args:
        raw_score: Raw total score from the LLM scoring agent.

    Returns:
        Score clamped to [0.0, 12.0].
    """
    if raw_score < 0.0:
        return 0.0
    if raw_score > 12.0:
        return 12.0
    return raw_score


def score_to_color(score: float) -> str:
    """Map a 0-12 AutoSCORE total to an Obsidian Canvas color code.

    Thresholds (proportional to old 0-100 scale):
      >= 10  -> "2" (green, mastered / passed)
      >= 7   -> "3" (purple, partial understanding / needs review)
      < 7    -> "4" (red, not understood / failed)

    These correspond to the old 80/100, 60/100 thresholds scaled to 12:
      80% of 12 = 9.6 -> rounded to 10
      60% of 12 = 7.2 -> rounded down to 7

    Args:
        score: Normalized total score in 0-12 range.

    Returns:
        Obsidian color code: "2" (green), "3" (purple), or "4" (red).
    """
    if score >= 10.0:
        return "2"  # green (mastered)
    elif score >= 7.0:
        return "3"  # purple (partial understanding)
    else:
        return "4"  # red (not understood)


def autoscore_to_percent(score_12: float) -> float:
    """Convert a 0-12 AutoSCORE total to a 0-100 percentage.

    Used when interfacing with subsystems that expect a 0-100 scale
    (e.g., FSRS get_rating_from_score).

    Args:
        score_12: Normalized score in 0-12 range.

    Returns:
        Percentage score in 0-100 range.
    """
    clamped = max(0.0, min(12.0, score_12))
    return round(clamped * 100.0 / 12.0, 2)
