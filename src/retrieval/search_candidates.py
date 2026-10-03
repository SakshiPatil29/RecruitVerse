"""
Candidate retrieval.

Three retrieval paths:
1. Uploaded batch — the resumes the recruiter just parsed, ranked by embedding
   similarity (works with no database).
2. Knowledge base — the dataset-backed FAISS index
   (src/knowledge_base/dataset_loader.py), also works with no database.
3. PostgreSQL + pgvector — every candidate saved earlier
   (src/database/load_candidates.py), only when USE_DATABASE=true. See
   src/retrieval/db_search.py: the recruiter's text is turned into filters
   (years, must-have skills) plus a meaning part; exact rules run as SQL and
   the meaning part ranks by cosine distance in the same query.

search_by_skill / search_by_experience / get_candidate are small exact
lookups on the same tables.

Candidate Search in the UI calls semantic_search.
"""

import logging

from src.config.settings import USE_DATABASE
from src.knowledge_base.dataset_loader import semantic_search as _kb_semantic_search

logger = logging.getLogger(__name__)


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
            ORDER BY c.experience_years DESC NULLS LAST, c.candidate_id
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
            ORDER BY experience_years DESC, candidate_id
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


def _semantic_rank_session(query, session_candidates, top_k, min_similarity=0.30):
    """Rank the recruiter's uploaded batch by real embedding similarity
    between the query and each candidate's resume/skills text, instead of
    literal substring overlap. This is what lets a query like "data
    visualization" surface a candidate whose resume only lists "Power BI"
    or "Tableau" — there is no shared keyword, but the embeddings place
    those phrases close together in meaning.

    Falls back to keyword-in-skills matching if the embedding model isn't
    available (see embedding_matcher.embeddings_available), so the page
    never goes silently empty on a machine without sentence-transformers.
    """
    from src.matching.embedding_matcher import (
        embeddings_available,
        embed_text,
        embed_texts,
        cosine_similarity,
    )

    query_lower = query.lower()

    if not embeddings_available():
        hits = []
        for candidate in session_candidates:
            skills_text = " ".join(candidate.get("skills", [])).lower()
            if any(word in skills_text or word in candidate.get("name", "").lower()
                   for word in query_lower.split()):
                hits.append({**candidate, "source": "uploaded_batch"})
        return hits

    texts = [
        " ".join(candidate.get("skills", [])) or candidate.get("raw_text", "") or candidate.get("name", "")
        for candidate in session_candidates
    ]
    if not texts:
        return []

    query_vec = embed_text(query)
    candidate_vecs = embed_texts(texts)

    scored = []
    for candidate, vec in zip(session_candidates, candidate_vecs):
        similarity = cosine_similarity(query_vec, vec)
        skills_text = " ".join(candidate.get("skills", [])).lower()
        keyword_hit = any(word in skills_text or word in candidate.get("name", "").lower()
                           for word in query_lower.split())
        # A keyword hit is a guaranteed strong signal (exact term used);
        # otherwise rely purely on semantic distance so related-but-not-
        # identical skills (e.g. query "data visualization" vs resume
        # skill "Power BI") can still qualify.
        if keyword_hit or similarity >= min_similarity:
            scored.append((max(similarity, 0.99 if keyword_hit else similarity), candidate))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {**candidate, "source": "uploaded_batch", "similarity": round(score * 100, 1)}
        for score, candidate in scored[:top_k]
    ]


def semantic_search(query, session_candidates=None, top_k=10, min_experience=0):
    """Natural-language candidate search combining:
    - the recruiter's currently uploaded/ranked batch (session_candidates),
      ranked by real Sentence-Transformer embedding similarity (with a
      keyword fallback only if the embedding model is unavailable),
    - the dataset-backed knowledge base, for "find me a Data Engineer with
      Spark" style discovery beyond the current upload batch, and
    - candidates stored in PostgreSQL (pgvector), when USE_DATABASE=true.

    min_experience (years) is applied to the database search as a SQL filter;
    the UI applies it to the other two lists.
    """

    session_candidates = session_candidates or []
    session_hits = _semantic_rank_session(query, session_candidates, top_k)
    kb_hits = _kb_semantic_search(query, top_k=top_k)

    database_hits, database_info = [], None
    if USE_DATABASE:
        try:
            from src.retrieval.db_search import search_candidates_db

            found = search_candidates_db(query, top_k=top_k, min_years=min_experience or None)
            database_hits = found["matches"]
            database_info = {key: found[key] for key in ("filters", "source", "mode", "relaxed")}
        except Exception as exc:  # database down, pgvector missing, ...: never break the page
            logger.warning("Database candidate search failed: %s", exc)
            database_info = {"error": str(exc)}

    return {
        "uploaded_batch_matches": session_hits,
        "knowledge_base_matches": kb_hits,
        "database_matches": database_hits,
        "database_info": database_info,
    }
