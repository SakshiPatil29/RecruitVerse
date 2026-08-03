"""
Candidate retrieval.

Two retrieval paths:
1. Structured DB search (search_by_skill / search_by_experience /
   get_candidate) — only used when USE_DATABASE is enabled and candidates
   have been persisted (see src/database/load_candidates.py).
2. Knowledge-base semantic search (semantic_search) — natural-language
   queries over the dataset-backed vector index
   (src/knowledge_base/dataset_loader.py), which works standalone with no
   database at all.

Candidate Search in the UI calls semantic_search; the DB helpers remain
available for anything that specifically needs exact structured lookups.
"""

from src.config.settings import USE_DATABASE
from src.knowledge_base.dataset_loader import semantic_search as _kb_semantic_search


def search_by_skill(skill):
    from src.config.db import get_connection

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT DISTINCT
                c.candidate_id, c.name, c.experience_years
            FROM candidates c
            JOIN candidate_skills s ON c.candidate_id = s.candidate_id
            WHERE LOWER(s.skill) = LOWER(%s)
            LIMIT 20
            """,
            (skill,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def search_by_experience(years):
    from src.config.db import get_connection

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT candidate_id, name, experience_years
            FROM candidates
            WHERE experience_years >= %s
            LIMIT 20
            """,
            (years,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_candidate(candidate_id):
    from src.config.db import get_connection

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM candidates WHERE candidate_id = %s", (candidate_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def semantic_search(query, session_candidates=None, top_k=10):
    """Natural-language candidate search combining:
    - the recruiter's currently uploaded/ranked batch (session_candidates),
      scored by simple keyword-in-skills relevance so an exact JD-batch
      match always surfaces first, and
    - the dataset-backed knowledge base, for "find me a Data Engineer with
      Spark" style discovery beyond the current upload batch.
    """

    session_candidates = session_candidates or []
    query_lower = query.lower()

    session_hits = []
    for candidate in session_candidates:
        skills_text = " ".join(candidate.get("skills", [])).lower()
        if any(word in skills_text or word in candidate.get("name", "").lower() for word in query_lower.split()):
            session_hits.append({**candidate, "source": "uploaded_batch"})

    kb_hits = _kb_semantic_search(query, top_k=top_k)

    return {
        "uploaded_batch_matches": session_hits,
        "knowledge_base_matches": kb_hits,
    }
