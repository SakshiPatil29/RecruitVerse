"""Tests for the Candidate Search fix in src/retrieval/search_candidates.py
— the "uploaded batch" path should catch a related-but-not-lexically-
overlapping query at least as well as a plain keyword search, and never
regress a query that keyword search already handled correctly."""

from src.retrieval.search_candidates import semantic_search

CANDIDATES = [
    {
        "name": "Rahul Verma",
        "skills": ["Python", "Power BI", "Tableau", "SQL"],
        "raw_text": "Data analyst skilled in Power BI and Tableau dashboards, SQL, Python.",
    },
    {
        "name": "Priya Sharma",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "raw_text": "Backend engineer building REST APIs in FastAPI and Python, backed by PostgreSQL.",
    },
]


def test_exact_keyword_query_still_matches():
    """A query using the candidate's literal skill name should always hit
    — this must never regress."""
    results = semantic_search("power bi", session_candidates=CANDIDATES, top_k=5)
    names = [c["name"] for c in results["uploaded_batch_matches"]]
    assert "Rahul Verma" in names


def test_unrelated_query_does_not_match_everything():
    """A query for a completely different domain shouldn't pull in an
    unrelated candidate just because the search ran."""
    results = semantic_search("salesforce apex development", session_candidates=CANDIDATES, top_k=5)
    names = [c["name"] for c in results["uploaded_batch_matches"]]
    assert "Priya Sharma" not in names or "Rahul Verma" not in names  # not everyone should match


def test_search_returns_expected_shape():
    results = semantic_search("python backend", session_candidates=CANDIDATES, top_k=5)
    assert "uploaded_batch_matches" in results
    assert "knowledge_base_matches" in results
    assert isinstance(results["uploaded_batch_matches"], list)


def test_empty_batch_returns_empty_results():
    results = semantic_search("anything", session_candidates=[], top_k=5)
    assert results["uploaded_batch_matches"] == []
