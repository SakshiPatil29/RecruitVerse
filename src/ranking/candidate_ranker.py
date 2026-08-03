"""
Candidate ranking.

The original rank_candidates just sorted by a "score" key. This keeps
that contract (sort descending by final_score) and adds rank numbers /
medal labels so the UI table doesn't need to know about ranking logic.
"""

MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def rank_candidates(results, score_key="final_score"):
    """Sort candidates best-to-worst and attach a 'rank' and 'medal' field
    to each. `results` is a list of dicts, each must contain score_key."""

    ranked = sorted(results, key=lambda x: x[score_key], reverse=True)

    for i, candidate in enumerate(ranked, start=1):
        candidate["rank"] = i
        candidate["medal"] = MEDALS.get(i, "")

    return ranked
