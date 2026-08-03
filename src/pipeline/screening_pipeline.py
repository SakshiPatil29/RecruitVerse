"""
Screening pipeline — the heart of the ATS workflow.

Given a parsed job description and a list of parsed resumes, this runs the
full deterministic pipeline the spec describes:

    resume parsing  ->  semantic matching  ->  skill extraction
                    ->  candidate ranking   ->  candidate analysis

It stitches together the individual modules (embedding_matcher,
skill_matcher, scoring_engine, candidate_ranker, score_explainer) so the
UI and the API share one code path and can't drift apart. No LLM calls
happen here — this stage is fully deterministic and reproducible. AI
narrative (summaries, questions, etc.) is layered on separately, on
demand, from src/ai/insights.py.
"""

from src.explainability.score_explainer import explain_score
from src.matching.embedding_matcher import rank_by_semantic_similarity
from src.matching.skill_matcher import match_skills
from src.ranking.candidate_ranker import rank_candidates
from src.ranking.scoring_engine import calculate_final_score, experience_score


def screen_candidates(jd, resumes):
    """Score and rank a batch of parsed resumes against a parsed JD.

    Args:
        jd: dict from jd_parser (required_skills, preferred_skills,
            experience_years, education, raw_text, ...).
        resumes: list of dicts from resume_parser (skills, experience_years,
            raw_text, name, ...).

    Returns:
        A ranked list of candidate dicts, each enriched with match analysis
        (matched/missing/additional skills, component scores, final score,
        rank, medal, and a structured explanation).
    """

    if not resumes:
        return []

    required_skills = jd.get("required_skills", [])
    preferred_skills = jd.get("preferred_skills", [])
    required_years = jd.get("experience_years", 0) or 0
    jd_text = jd.get("raw_text", "")

    # One batched embedding call for the whole cohort (JD embedded once).
    resume_texts = [r.get("raw_text", "") for r in resumes]
    semantic_scores = rank_by_semantic_similarity(resume_texts, jd_text)

    scored = []
    for resume, semantic_score in zip(resumes, semantic_scores):
        skill_result = match_skills(
            resume.get("skills", []),
            required_skills,
            preferred_skills,
        )

        candidate_years = resume.get("experience_years", 0) or 0
        exp_score = experience_score(candidate_years, required_years)
        exp_ok = candidate_years >= required_years if required_years else True

        final_score = calculate_final_score(
            skill_result["skill_score"],
            semantic_score,
            exp_score,
        )

        explanation = explain_score(
            skill_result["matched_skills"],
            skill_result["missing_skills"],
            semantic_score,
            exp_ok=exp_ok,
            required_years=required_years,
            candidate_years=candidate_years,
        )

        candidate = {
            **resume,
            "matched_skills": skill_result["matched_skills"],
            "missing_skills": skill_result["missing_skills"],
            "additional_skills": skill_result["additional_skills"],
            "skill_score": skill_result["skill_score"],
            "semantic_score": semantic_score,
            "experience_score": exp_score,
            "final_score": final_score,
            "explanation": explanation,
        }
        scored.append(candidate)

    return rank_candidates(scored, score_key="final_score")
