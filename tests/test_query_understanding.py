"""Tests for src/retrieval/query_understanding.py — no database, no network.

The recruiter's search text becomes filters (years, must-have skills) plus a
meaning part. Groq's JSON is validated before use, and a regex parser takes
over whenever Groq is missing or returns something unusable."""

import pytest

from src.retrieval import query_understanding as qu


# ---------- regex fallback parser ----------

@pytest.mark.parametrize("text, expected", [
    ("candidates with 3+ years of experience", {"min_years": 3}),
    ("at least 5 years Spark and Airflow", {"min_years": 5, "semantic_text": "Spark Airflow"}),
    ("2-4 years data engineer", {"min_years": 2, "max_years": 4, "semantic_text": "data engineer"}),
    ("Python developer with Kafka experience", {"semantic_text": "Python developer Kafka experience"}),
    ("freshers with Java", {"max_years": 1, "semantic_text": "freshers Java"}),
])
def test_regex_parser(text, expected):
    assert qu.parse_query_regex(text) == expected


# ---------- validation of model output ----------

def test_valid_json_is_kept_and_skills_are_normalised():
    out = qu.validate_filters('{"min_years": 3, "skills": ["Python", "ML"], "semantic_text": "backend developer"}')
    assert out == {"min_years": 3, "skills": ["python", "machine learning"], "semantic_text": "backend developer"}


def test_code_fence_is_removed():
    assert qu.validate_filters('```json\n{"min_years": 2}\n```') == {"min_years": 2}


def test_unknown_keys_and_wrong_types_are_dropped():
    raw = '{"min_years": "3; DROP TABLE candidates", "sql": "DELETE FROM candidates", "max_years": 5}'
    assert qu.validate_filters(raw) == {"max_years": 5}


@pytest.mark.parametrize("raw", [
    "Sure! SELECT * FROM candidates", "[]", "", None,
    '{"min_years": 9, "max_years": 2}',          # contradictory
])
def test_unusable_replies_return_none(raw):
    assert qu.validate_filters(raw) is None


def test_out_of_range_years_are_ignored():
    assert qu.validate_filters('{"min_years": 500}') == {}


# ---------- choosing between Groq and the regex parser ----------

def test_uses_groq_json_when_available(monkeypatch):
    monkeypatch.setattr(qu, "USE_LLM_QUERY_PARSER", True)
    monkeypatch.setattr(qu, "is_available", lambda: True)
    monkeypatch.setattr(qu, "generate", lambda *a, **k: '{"min_years": 4, "skills": ["kafka"]}')
    filters, source = qu.extract_filters("kafka people, 4 years")
    assert source == "llm" and filters == {"min_years": 4, "skills": ["kafka"]}


def test_falls_back_to_regex_when_groq_reply_is_invalid(monkeypatch):
    monkeypatch.setattr(qu, "USE_LLM_QUERY_PARSER", True)
    monkeypatch.setattr(qu, "is_available", lambda: True)
    monkeypatch.setattr(qu, "generate", lambda *a, **k: "I cannot help with that")
    filters, source = qu.extract_filters("at least 5 years python")
    assert source == "regex" and filters["min_years"] == 5


def test_falls_back_to_regex_when_groq_call_fails(monkeypatch):
    monkeypatch.setattr(qu, "USE_LLM_QUERY_PARSER", True)
    monkeypatch.setattr(qu, "is_available", lambda: True)
    monkeypatch.setattr(qu, "generate", lambda *a, **k: None)      # groq_client returns None on any failure
    assert qu.extract_filters("python developer")[1] == "regex"


def test_regex_used_when_no_groq_key(monkeypatch):
    monkeypatch.setattr(qu, "is_available", lambda: False)
    filters, source = qu.extract_filters("3+ years")
    assert source == "regex" and filters == {"min_years": 3}


def test_llm_parser_can_be_switched_off(monkeypatch):
    monkeypatch.setattr(qu, "USE_LLM_QUERY_PARSER", False)
    monkeypatch.setattr(qu, "is_available", lambda: True)
    monkeypatch.setattr(qu, "generate", lambda *a, **k: pytest.fail("Groq must not be called"))
    assert qu.extract_filters("python")[1] == "regex"


def test_text_that_yields_nothing_is_kept_as_meaning(monkeypatch):
    monkeypatch.setattr(qu, "is_available", lambda: False)
    assert qu.extract_filters("and with")[0] == {"semantic_text": "and with"}
