"""
Core test suite for the ATS pipeline.

Covers the deterministic path end-to-end (parse -> skill match -> score ->
rank) without needing a database, Ollama, or network access. The
embedding model is heavy to load, so pipeline tests that need semantic
scores monkeypatch the embedding step — the goal here is to verify the
orchestration and math, not to benchmark the transformer.
"""

import pytest

from src.matching.skill_extractor import extract_skills
from src.matching.skill_matcher import match_skills
from src.parser.jd_parser import parse_jd_text
from src.parser.resume_parser import parse_resume_text
from src.ranking.candidate_ranker import rank_candidates
from src.ranking.scoring_engine import calculate_final_score, experience_score


# ---------- skill extraction ----------

def test_extract_skills_finds_known_skills():
    skills = extract_skills("Experienced with Python, SQL and AWS.")
    assert "Python" in skills
    assert "SQL" in skills


# ---------- skill matching ----------

def test_match_skills_full_and_missing():
    result = match_skills(
        resume_skills=["Python", "SQL"],
        required_skills=["Python", "SQL", "AWS"],
        preferred_skills=["Docker"],
    )
    assert "Python" in result["matched_skills"]
    assert "AWS" in result["missing_skills"]
    assert result["skill_score"] == pytest.approx(66.67, abs=0.1)


def test_match_skills_additional():
    result = match_skills(
        resume_skills=["Python", "Kafka"],
        required_skills=["Python"],
        preferred_skills=[],
    )
    assert "Kafka" in result["additional_skills"]
    assert result["skill_score"] == 100.0


# ---------- scoring ----------

def test_experience_score_meets_requirement():
    assert experience_score(5, 3) == 100.0
    assert experience_score(1, 4) == pytest.approx(25.0)
    assert experience_score(2, 0) == 100.0  # no requirement


def test_calculate_final_score_weighted():
    score = calculate_final_score(skill_score=100, semantic_score=50, exp_score=100)
    # 100*0.5 + 50*0.3 + 100*0.2 = 85
    assert score == 85.0


# ---------- ranking ----------

def test_rank_candidates_orders_and_medals():
    ranked = rank_candidates([
        {"name": "A", "final_score": 60},
        {"name": "B", "final_score": 90},
        {"name": "C", "final_score": 75},
    ])
    assert [c["name"] for c in ranked] == ["B", "C", "A"]
    assert ranked[0]["medal"] == "🥇"
    assert ranked[0]["rank"] == 1


# ---------- parsing ----------

def test_parse_resume_text_structured_fields():
    text = "Jane Doe\njane@example.com\n5 years experience\nSkills: Python, SQL"
    parsed = parse_resume_text(text)
    assert parsed["email"] == "jane@example.com"
    assert parsed["experience_years"] == 5
    assert "Python" in parsed["skills"]


def test_parse_jd_splits_required_and_preferred():
    text = "Required Skills: Python, SQL. Nice to have: AWS."
    jd = parse_jd_text(text)
    assert "Python" in jd["required_skills"]
    assert "AWS" in jd["preferred_skills"]
    assert "AWS" not in jd["required_skills"]


# ---------- pipeline (embedding step patched) ----------

def test_screening_pipeline_end_to_end(monkeypatch):
    import src.pipeline.screening_pipeline as sp

    # Stub the embedding call so the test doesn't load the transformer.
    monkeypatch.setattr(sp, "rank_by_semantic_similarity", lambda texts, jd: [80.0 for _ in texts])

    jd = parse_jd_text("Required Skills: Python, SQL, AWS. 3 years experience.")
    resumes = [
        parse_resume_text("Alice\n5 years experience\nPython SQL AWS"),
        parse_resume_text("Bob\n1 years experience\nPython"),
    ]

    ranked = sp.screen_candidates(jd, resumes)
    assert len(ranked) == 2
    assert ranked[0]["final_score"] >= ranked[1]["final_score"]
    assert ranked[0]["rank"] == 1
    assert "matched_skills" in ranked[0]
    assert "explanation" in ranked[0]
