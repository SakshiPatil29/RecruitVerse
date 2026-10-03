"""
Final score calculation.

Replaces the original calculate_score (which was just skill-overlap
percentage) with a weighted blend of skill match, semantic similarity,
and experience relevance — using the weights already defined in
src/explainability/feature_importance.FEATURE_WEIGHTS (kept as the
single source of truth, re-exported from settings for convenience).
"""

from src.config.settings import RANKING_WEIGHTS


def experience_score(candidate_years, required_years):
    """0-100 score for how a candidate's experience compares to the JD's
    stated requirement. Meeting or exceeding the requirement scores 100;
    falling short scores proportionally, never negative."""

    if not required_years or required_years <= 0:
        return 100.0

    if candidate_years >= required_years:
        return 100.0

    return round((candidate_years / required_years) * 100, 2)


def calculate_final_score(skill_score, semantic_score, exp_score, weights=None):
    """Weighted final match score (0-100)."""
    weights = weights or RANKING_WEIGHTS

    final = (
        skill_score * weights["skill_match"]
        + semantic_score * weights["semantic_similarity"]
        + exp_score * weights["experience"]
    )
    return round(final, 2)


# Kept for backward compatibility with anything importing the original
# simple skill-overlap calculation directly.
def calculate_score(matched_skills, jd_skills):
    if len(jd_skills) == 0:
        return 0
    score = (len(matched_skills) / len(jd_skills)) * 100
    return round(score, 2)
