"""
Skill matching.

Builds on the original jd_matcher.py logic (matched = intersection,
missing = JD skills not on the resume) and adds "additional skills" —
skills the candidate has that the JD didn't ask for — which the spec
calls out as its own category and the original codebase never tracked.
"""

from src.matching.semantic_matcher import normalize_skill


def match_skills(resume_skills, required_skills, preferred_skills=None):
    """Compare a resume's skills against a JD's required + preferred
    skills. Returns matched, missing (required only), and additional
    skills, plus a required-skill coverage score (0-100)."""

    preferred_skills = preferred_skills or []

    resume_norm = {normalize_skill(s): s for s in resume_skills}
    required_norm = {normalize_skill(s): s for s in required_skills}
    preferred_norm = {normalize_skill(s): s for s in preferred_skills}
    jd_norm_keys = set(required_norm) | set(preferred_norm)

    matched_keys = set(resume_norm) & jd_norm_keys
    missing_required_keys = set(required_norm) - set(resume_norm)
    additional_keys = set(resume_norm) - jd_norm_keys

    matched = sorted(required_norm.get(k, preferred_norm.get(k)) for k in matched_keys)
    missing = sorted(required_norm[k] for k in missing_required_keys)
    additional = sorted(resume_norm[k] for k in additional_keys)

    required_count = len(required_norm)
    matched_required_count = len(set(required_norm) & set(resume_norm))
    skill_score = round((matched_required_count / required_count) * 100, 2) if required_count else 100.0

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "additional_skills": additional,
        "skill_score": skill_score,
    }
