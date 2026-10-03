SKILL_SYNONYMS = {

    "ml":
    "machine learning",

    "ai":
    "artificial intelligence",

    "js":
    "javascript",

    "pyspark":
    "spark",

    "nlp":
    "natural language processing"
}
    
def normalize_skill(skill):

    skill = skill.lower().strip()

    return SKILL_SYNONYMS.get(
        skill,
        skill
    )

def semantic_match(
        resume_skills,
        jd_skills):

    resume_normalized = {

        normalize_skill(skill)

        for skill in resume_skills
    }

    jd_normalized = {

        normalize_skill(skill)

        for skill in jd_skills
    }

    matched = (
        resume_normalized
        &
        jd_normalized
    )

    missing = (
        jd_normalized
        -
        resume_normalized
    )

    score = (
        len(matched)
        /
        len(jd_normalized)
    ) * 100

    return {

        "matched":
        list(matched),

        "missing":
        list(missing),

        "score":
        round(score, 2)
    }