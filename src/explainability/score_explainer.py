"""
Deterministic score explanation.

Every score must be explainable per the spec — and explainability can't
depend on the LLM being reachable, so this produces a structured ✓/✗
reason list from the same matched/missing skill + experience data that
fed the score. src/ai/insights.generate_explanation builds a fuller
prose explanation on top of this when Ollama is available.
"""


def explain_score(matched_skills, missing_skills, semantic_score, exp_ok=True, required_years=0, candidate_years=0):
    reasons = []

    for skill in matched_skills:
        reasons.append({"ok": True, "text": f"{skill} matched"})

    for skill in missing_skills:
        reasons.append({"ok": False, "text": f"{skill} missing"})

    if required_years:
        if exp_ok:
            reasons.append({
                "ok": True,
                "text": f"Experience requirement satisfied ({candidate_years} yrs vs {required_years} yrs required)",
            })
        else:
            reasons.append({
                "ok": False,
                "text": f"Experience below requirement ({candidate_years} yrs vs {required_years} yrs required)",
            })

    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "semantic_score": semantic_score,
        "reasons": reasons,
    }


def generate_reason(score, matched_skills, missing_skills):
    """Plain-text fallback explanation (kept for any code/tests that want
    a single string rather than the structured dict above)."""

    return (
        f"Candidate scored {score}. "
        f"Matched skills: {', '.join(matched_skills) if matched_skills else 'none'}. "
        f"Missing skills: {', '.join(missing_skills) if missing_skills else 'none'}."
    )
