"""PostgreSQL + pgvector candidate search, end to end.

These tests need a real PostgreSQL server with the pgvector extension, so they
are skipped unless you point them at one:

    TEST_DATABASE_ADMIN_URL=postgresql://postgres:postgres@localhost:5432/postgres pytest tests/test_db_search.py

A throw-away database is created for the run and dropped afterwards. A small
deterministic fake embedder replaces the Sentence-Transformers model, so no
model download is needed (similarity values here are NOT real MiniLM values).
"""

import hashlib
import os
import re

import numpy as np
import pytest

ADMIN_URL = os.getenv("TEST_DATABASE_ADMIN_URL")
pytestmark = pytest.mark.skipif(not ADMIN_URL, reason="set TEST_DATABASE_ADMIN_URL to run PostgreSQL tests")

TEST_DB = "recruitverse_search_test"
DIM = 384


def fake_embed(text):
    """Sum of one random vector per word, normalised: shared words => similar vectors."""
    vec = np.zeros(DIM, dtype=np.float32)
    for token in re.findall(r"[a-z0-9+#.]+", text.lower()):
        seed = int(hashlib.md5(token.encode()).hexdigest()[:8], 16)
        vec += np.random.default_rng(seed).normal(size=DIM).astype(np.float32)
    norm = np.linalg.norm(vec)
    return vec / norm if norm else vec


PEOPLE = [
    {"name": "Asha", "email": "asha@example.com", "title": "Backend developer", "education": "B.Tech",
     "experience_years": 4, "skills": ["Python", "Kafka", "SQL"]},
    {"name": "Ravi", "email": "ravi@example.com", "title": "Data engineer", "education": "M.Tech",
     "experience_years": 7, "skills": ["Python", "Spark", "Airflow", "ML"]},
    {"name": "Meera", "email": "meera@example.com", "title": "Data analyst", "education": "B.Sc",
     "experience_years": 1, "skills": ["SQL", "Power BI", "Excel"]},
    {"name": "John", "email": "john@example.com", "title": "ML engineer", "education": "PhD",
     "experience_years": 9, "skills": ["Python", "scikit-learn", "Machine Learning"]},
    {"name": "Nina", "email": "nina@example.com", "title": "Fresher", "education": "B.E",
     "experience_years": None, "skills": ["Java"]},
]


@pytest.fixture(scope="module")
def env():
    import psycopg2

    admin = psycopg2.connect(ADMIN_URL)
    admin.autocommit = True
    with admin.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}")
        cur.execute(f"CREATE DATABASE {TEST_DB}")

    test_url = ADMIN_URL.rsplit("/", 1)[0] + "/" + TEST_DB
    mp = pytest.MonkeyPatch()
    mp.setenv("DATABASE_URL", test_url)

    schema = open(os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql"), encoding="utf-8").read()
    conn = psycopg2.connect(test_url)
    with conn, conn.cursor() as cur:
        cur.execute(schema)
    conn.close()

    from src.database import load_candidates
    from src.retrieval import db_search, query_understanding

    mp.setattr(load_candidates, "_embed_profile", lambda text: fake_embed(text) if text else None)
    mp.setattr(db_search, "_embed", fake_embed)
    mp.setattr(db_search, "_embeddings_ready", lambda: True)
    mp.setattr(query_understanding, "is_available", lambda: False)      # regex parser unless a test overrides

    from src.config.db import db_session

    with db_session() as c:
        cur = c.cursor()
        for person in PEOPLE:
            load_candidates.insert_candidate(cur, person)

    yield mp

    mp.undo()
    with admin.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}")
    admin.close()


def names(result):
    return [m["name"] for m in result["matches"]]


def test_loading_twice_updates_instead_of_duplicating(env):
    from src.config.db import db_session
    from src.database.load_candidates import insert_candidate

    with db_session() as conn:
        cur = conn.cursor()
        insert_candidate(cur, {**PEOPLE[0], "email": "ASHA@example.com", "experience_years": 5})
        cur.execute("SELECT count(*) FROM candidates")
        assert cur.fetchone()[0] == len(PEOPLE)
        cur.execute("SELECT experience_years FROM candidates WHERE LOWER(email) = 'asha@example.com'")
        assert cur.fetchone()[0] == 5
        insert_candidate(cur, PEOPLE[0])             # put it back for the other tests


def test_aliases_are_stored_in_full_form(env):
    from src.config.db import db_session

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT count(*) FROM candidate_skills s JOIN candidates c USING (candidate_id)
                       WHERE c.name = 'Ravi' AND s.skill = 'machine learning'""")
        assert cur.fetchone()[0] == 1


def test_years_only_query_uses_plain_sql(env):
    from src.retrieval.db_search import search_candidates_db

    out = search_candidates_db("candidates with 5+ years of experience")
    assert out["mode"] == "filters" and names(out) == ["John", "Ravi"]
    assert all(m["experience_years"] >= 5 for m in out["matches"])


def test_null_experience_is_excluded_by_a_years_rule(env):
    from src.retrieval.db_search import search_candidates_db

    assert "Nina" not in names(search_candidates_db("0+ years"))


def test_meaning_query_ranks_by_pgvector_distance(env):
    from src.retrieval.db_search import search_candidates_db

    out = search_candidates_db("Python Kafka backend developer", min_similarity=0.0)
    assert out["mode"] == "vector" and names(out)[0] == "Asha"
    assert out["matches"][0]["similarity"] is not None


def test_must_have_skills_are_exact_and_alias_aware(env, monkeypatch):
    from src.retrieval import query_understanding as qu
    from src.retrieval.db_search import search_candidates_db

    monkeypatch.setattr(qu, "USE_LLM_QUERY_PARSER", True)
    monkeypatch.setattr(qu, "is_available", lambda: True)
    monkeypatch.setattr(qu, "generate", lambda *a, **k:
                        '{"min_years": 3, "skills": ["python", "ML"], "semantic_text": "data engineer"}')
    out = search_candidates_db("python and ml, 3 years, data engineer", min_similarity=-1.0)
    assert out["source"] == "llm" and set(names(out)) == {"Ravi", "John"} and names(out)[0] == "Ravi"


def test_missing_skills_relax_to_meaning_and_say_so(env, monkeypatch):
    from src.retrieval import query_understanding as qu
    from src.retrieval.db_search import search_candidates_db

    monkeypatch.setattr(qu, "USE_LLM_QUERY_PARSER", True)
    monkeypatch.setattr(qu, "is_available", lambda: True)
    monkeypatch.setattr(qu, "generate", lambda *a, **k: '{"skills": ["cobol", "fortran"], "semantic_text": "mainframe"}')
    out = search_candidates_db("cobol fortran mainframe", min_similarity=-1.0)
    assert out["relaxed"] is True and out["matches"]


def test_ui_minimum_experience_is_applied_in_sql(env):
    from src.retrieval.db_search import search_candidates_db

    out = search_candidates_db("Python developer", min_years=8, min_similarity=-1.0)
    assert names(out) == ["John"]


def test_keyword_fallback_when_embeddings_are_unavailable(env, monkeypatch):
    from src.retrieval import db_search

    monkeypatch.setattr(db_search, "_embeddings_ready", lambda: False)
    out = db_search.search_candidates_db("spark airflow")
    assert out["mode"] == "keyword" and names(out)[0] == "Ravi"


def test_hostile_and_empty_input_are_safe(env):
    from src.config.db import db_session
    from src.retrieval.db_search import search_candidates_db

    search_candidates_db("'; DROP TABLE candidates; --")
    assert search_candidates_db("   ")["matches"] == []
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM candidates")
        assert cur.fetchone()[0] == len(PEOPLE)


def test_semantic_search_returns_the_database_section(env, monkeypatch):
    from src.retrieval import search_candidates

    monkeypatch.setattr(search_candidates, "USE_DATABASE", True)
    monkeypatch.setattr(search_candidates, "_kb_semantic_search", lambda q, top_k=10: [])
    out = search_candidates.semantic_search("5+ years", session_candidates=[], top_k=5)
    assert {m["name"] for m in out["database_matches"]} == {"John", "Ravi"}
    assert out["database_info"]["mode"] == "filters"


def test_database_failure_never_breaks_the_page(env, monkeypatch):
    from src.retrieval import search_candidates

    monkeypatch.setattr(search_candidates, "USE_DATABASE", True)
    monkeypatch.setattr(search_candidates, "_kb_semantic_search", lambda q, top_k=10: [])
    monkeypatch.setenv("DATABASE_URL", "postgresql://nobody:wrong@localhost:1/none")
    out = search_candidates.semantic_search("python", session_candidates=[], top_k=5)
    assert out["database_matches"] == [] and "error" in out["database_info"]


def test_sample_parsed_resumes_load(env):
    from src.database.load_candidates import process_all_json

    assert process_all_json() >= 4                 # the four sample resumes shipped in data/parsed_resumes


def test_persist_parsed_resumes_reports_errors_instead_of_raising(env, monkeypatch):
    from src.database.load_candidates import persist_parsed_resumes

    ok = persist_parsed_resumes([{"name": "Tara", "email": "tara@example.com", "skills": ["Go"], "experience_years": 2}])
    assert ok == {"stored": 1, "error": None}
    monkeypatch.setenv("DATABASE_URL", "postgresql://nobody:wrong@localhost:1/none")
    bad = persist_parsed_resumes([{"name": "X"}])
    assert bad["stored"] == 0 and bad["error"]
