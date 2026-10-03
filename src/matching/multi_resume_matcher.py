from src.matching.jd_matcher import (
    match_resume_jd
)


def process_resumes(
        resumes,
        jd_text):

    results = []

    for resume in resumes:

        result = match_resume_jd(
            resume["text"],
            jd_text
        )

        result[
            "resume_name"
        ] = resume[
            "resume_name"
        ]

        results.append(
            result
        )

    return results