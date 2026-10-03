from src.matching.skill_extractor import extract_skills


def match_resume_jd(
        resume_text,
        jd_text):

    resume_skills = set(
        extract_skills(
            resume_text
        )
    )

    jd_skills = set(
        extract_skills(
            jd_text
        )
    )

    matched = resume_skills.intersection(
        jd_skills
    )

    missing = jd_skills - resume_skills

    if len(jd_skills) == 0:

        score = 0

    else:

        score = (
            len(matched)
            /
            len(jd_skills)
        ) * 100

    return {

        "matched_skills":
        list(matched),

        "missing_skills":
        list(missing),

        "score":
        round(score, 2)
    }