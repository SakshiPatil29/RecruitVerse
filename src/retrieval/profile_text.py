"""Candidate profile text and skill normalisation for database search.

The text built here is what gets embedded and stored in candidates.embedding.
We embed a short profile (skills, education, experience) instead of the whole
resume: resumes are long and noisy, and all-MiniLM-L6-v2 only reads about 256
tokens, so a compact summary of what recruiters search for works better.
"""

import re

# Short forms recruiters type vs the form stored. SQL equality cannot see that
# "ML" and "machine learning" are the same thing, so both loading and searching
# map them to one spelling. Semantic search covers everything not listed here.
SKILL_ALIASES = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "js": "javascript",
    "postgres": "postgresql",
    "py": "python",
    "sklearn": "scikit-learn",
}


def skill_key(skill):
    """Lower-case, single-spaced, alias-resolved form used for MATCHING."""
    key = " ".join(str(skill).lower().split())
    return SKILL_ALIASES.get(key, key)


def canonical_skill(skill):
    """Form that is STORED: the original wording, except known aliases which
    are replaced by their full name so SQL equality works."""
    text = " ".join(str(skill).split())
    key = text.lower()
    return SKILL_ALIASES.get(key, text)


def canonical_skills(skills):
    """Clean, de-duplicated (case-insensitive) list of stored skill names."""
    seen, out = set(), []
    for skill in skills or []:
        if not str(skill).strip():
            continue
        name = canonical_skill(skill)
        key = name.lower()
        if key not in seen:
            seen.add(key)
            out.append(name)
    return out


def skill_keys(skills):
    """De-duplicated matching keys for a list of skills."""
    seen, out = set(), []
    for skill in skills or []:
        key = skill_key(skill)
        if key and key not in seen:
            seen.add(key)
            out.append(key)
    return out


def build_profile_text(candidate):
    """Short text describing a candidate, e.g.
    "Backend developer. Skills: python, fastapi. Education: B.Tech. Experience: 2 years."
    Returns "" when there is nothing worth embedding (empty text would give a
    zero vector and a NaN distance)."""
    skills = canonical_skills(candidate.get("skills"))
    parts = []

    title = candidate.get("title") or candidate.get("category")
    if title:
        parts.append(str(title).strip().rstrip(".") + ".")
    if skills:
        parts.append("Skills: " + ", ".join(skills[:40]) + ".")
    if candidate.get("education"):
        parts.append("Education: " + str(candidate["education"]).strip() + ".")

    years = candidate.get("experience_years")
    if years is not None and str(years) != "":
        unit = "year" if str(years) == "1" else "years"
        parts.append(f"Experience: {years} {unit}.")

    text = " ".join(parts)
    return re.sub(r"\s+", " ", text).strip() if (skills or title) else ""
