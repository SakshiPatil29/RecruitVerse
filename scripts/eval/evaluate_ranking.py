"""
Ranking ablation study: shows what each of the 3 scoring components
(skill match, semantic similarity, experience) actually contributes, by
re-ranking the same candidate batch with each weight combination in turn.

Usage:
    python -m scripts.eval.evaluate_ranking

The headline case: a candidate who describes a skill in different words
than the JD (e.g. resume says "BI dashboards in Power BI", JD asks for
"data visualization experience") should still rank reasonably under the
semantic component even though skill-only scoring can't see the overlap.
"""

from src.matching.embedding_matcher import semantic_backend
from src.matching.skill_matcher import match_skills
from src.matching.embedding_matcher import rank_by_semantic_similarity
from src.ranking.scoring_engine import calculate_final_score, experience_score
from scripts.eval.sample_candidates import CANDIDATES

JD = {
    "required_skills": ["SQL", "Data Visualization", "Excel"],
    "preferred_skills": ["Python"],
    "experience_years": 2,
    "raw_text": (
        "We are hiring an analyst with strong data visualization experience to build "
        "dashboards and reports for leadership. Must be comfortable with SQL and Excel; "
        "Python is a plus."
    ),
}

WEIGHT_SETS = {
    "Skill-only   (1.0 / 0.0 / 0.0)": {"skill_match": 1.0, "semantic_similarity": 0.0, "experience": 0.0},
    "Semantic-only (0.0 / 1.0 / 0.0)": {"skill_match": 0.0, "semantic_similarity": 1.0, "experience": 0.0},
    "Actual blend  (0.5 / 0.3 / 0.2)": {"skill_match": 0.5, "semantic_similarity": 0.3, "experience": 0.2},
}


def main():
    print(f"Similarity backend in use: {semantic_backend()}")
    print(f"JD requires: {JD['required_skills']} (+ preferred: {JD['preferred_skills']})\n")

    resume_texts = [c["raw_text"] for c in CANDIDATES]
    semantic_scores = rank_by_semantic_similarity(resume_texts, JD["raw_text"])

    base_rows = []
    for candidate, semantic_score in zip(CANDIDATES, semantic_scores):
        skill_result = match_skills(candidate["skills"], JD["required_skills"], JD["preferred_skills"])
        exp_score = experience_score(candidate["experience_years"], JD["experience_years"])
        base_rows.append({
            "name": candidate["name"],
            "skill_score": skill_result["skill_score"],
            "semantic_score": semantic_score,
            "exp_score": exp_score,
        })

    for label, weights in WEIGHT_SETS.items():
        print(f"--- {label} ---")
        ranked = sorted(
            base_rows,
            key=lambda r: calculate_final_score(r["skill_score"], r["semantic_score"], r["exp_score"], weights),
            reverse=True,
        )
        for i, r in enumerate(ranked[:8], start=1):
            final = calculate_final_score(r["skill_score"], r["semantic_score"], r["exp_score"], weights)
            print(f"  {i}. {r['name']:<16} final={final:6.2f}  "
                  f"(skill={r['skill_score']:6.2f}  semantic={r['semantic_score']:6.2f}  exp={r['exp_score']:6.2f})")
        print()


if __name__ == "__main__":
    main()
