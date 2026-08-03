"""
Aggregate analytics over a ranked batch of candidates — feeds the
handful of charts the spec asks for (score distribution, top skills,
skill gap analysis, experience distribution). Deliberately narrow: the
old codebase had a dozen analytics dashboards for things unrelated to
resume ranking; this module only computes what the ATS UI shows.
"""

from collections import Counter


def score_distribution(candidates, score_key="final_score"):
    return [c[score_key] for c in candidates]


def top_skills(candidates, skill_key="matched_skills", top_n=10):
    counter = Counter()
    for c in candidates:
        counter.update(c.get(skill_key, []))
    return counter.most_common(top_n)


def skill_gap_analysis(candidates, missing_key="missing_skills", top_n=10):
    """Which required skills are missing most often across the batch —
    tells a recruiter what the candidate pool is collectively weak on."""
    counter = Counter()
    for c in candidates:
        counter.update(c.get(missing_key, []))
    return counter.most_common(top_n)


def experience_distribution(candidates, exp_key="experience_years"):
    return [c.get(exp_key, 0) for c in candidates]


def generate_analytics(candidates):
    """Convenience bundle used by the Dashboard page."""
    if not candidates:
        return {
            "avg_score": 0,
            "top_skills": [],
            "skill_gaps": [],
            "experience_distribution": [],
        }

    scores = score_distribution(candidates)
    return {
        "avg_score": round(sum(scores) / len(scores), 2),
        "top_skills": top_skills(candidates),
        "skill_gaps": skill_gap_analysis(candidates),
        "experience_distribution": experience_distribution(candidates),
    }
