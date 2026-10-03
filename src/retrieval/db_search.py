"""Candidate search over PostgreSQL + pgvector.

Flow for one recruiter query:

    free text
       -> query_understanding.extract_filters()      Llama JSON or regex fallback
       -> filters: min_years / max_years / skills (exact) + semantic_text (meaning)
       -> ONE parameterised SQL statement
             exact rules  -> WHERE
             meaning      -> ORDER BY embedding <=> query_vector   (pgvector, cosine distance)
       -> second query fetches the full details of the winners (name, email, skills ...)

Only used when USE_DATABASE=true. The structured data and the vectors live in
the same PostgreSQL database, so filters and similarity run in a single query.
"""

import logging
import re

from psycopg2.extras import RealDictCursor

from src.config.db import db_session
from src.config.settings import DB_SEARCH_MIN_SIMILARITY
from src.retrieval.query_understanding import extract_filters

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "on", "for", "to", "with", "who", "that",
    "have", "has", "having", "knowledge", "experience", "experienced", "skills", "skill",
    "developer", "engineer", "candidate", "candidates", "someone", "person", "people",
}


def _embeddings_ready():
    from src.matching.embedding_matcher import embeddings_available

    return embeddings_available()


def _embed(text):
    from src.matching.embedding_matcher import embed_text

    return embed_text(text)


def _where(filters, need_embedding):
    """Build the WHERE conditions. Values are always passed as parameters."""
    where, params = [], []
    if need_embedding:
        where.append("c.embedding IS NOT NULL")
    if "min_years" in filters:
        where.append("c.experience_years >= %s")
        params.append(filters["min_years"])
    if "max_years" in filters:
        where.append("c.experience_years <= %s")
        params.append(filters["max_years"])
    if filters.get("skills"):
        # candidate must have ALL listed skills
        where.append(
            """c.candidate_id IN (
                   SELECT candidate_id FROM candidate_skills
                   WHERE LOWER(skill) = ANY(%s)
                   GROUP BY candidate_id
                   HAVING COUNT(DISTINCT LOWER(skill)) = %s)"""
        )
        params += [filters["skills"], len(set(filters["skills"]))]
    return where, params


def _tokens(text):
    words = re.findall(r"[a-z0-9+#.]+", (text or "").lower())
    return [w for w in dict.fromkeys(words) if w not in _STOPWORDS and len(w) > 1]


def _rank_ids(cursor, filters, top_k, min_similarity):
    """Return ([(candidate_id, similarity_or_None), ...], mode)."""
    semantic = (filters.get("semantic_text") or "").strip()

    # 1. meaning: pgvector cosine distance
    if semantic and _embeddings_ready():
        where, params = _where(filters, need_embedding=True)
        query_vector = _embed(semantic)
        cursor.execute(
            f"""SELECT c.candidate_id, 1 - (c.embedding <=> %s) AS similarity
                FROM candidates c
                WHERE {' AND '.join(where)}
                ORDER BY c.embedding <=> %s
                LIMIT %s""",
            [query_vector] + params + [query_vector, top_k],
        )
        rows = [(r["candidate_id"], float(r["similarity"])) for r in cursor.fetchall()]
        return [r for r in rows if r[1] >= min_similarity], "vector"

    # 2. embeddings unavailable: plain skill-keyword match on the descriptive words
    tokens = _tokens(semantic)
    if tokens:
        where, params = _where(filters, need_embedding=False)
        where.append("LOWER(s.skill) = ANY(%s)")
        cursor.execute(
            f"""SELECT c.candidate_id, COUNT(DISTINCT LOWER(s.skill)) AS matched
                FROM candidates c JOIN candidate_skills s ON s.candidate_id = c.candidate_id
                WHERE {' AND '.join(where)}
                GROUP BY c.candidate_id, c.experience_years
                ORDER BY matched DESC, c.experience_years DESC NULLS LAST, c.candidate_id
                LIMIT %s""",
            params + [tokens, top_k],
        )
        return [(r["candidate_id"], None) for r in cursor.fetchall()], "keyword"

    # 3. only exact rules, e.g. "3+ years"
    where, params = _where(filters, need_embedding=False)
    if not where:
        return [], "none"
    cursor.execute(
        f"""SELECT c.candidate_id FROM candidates c
            WHERE {' AND '.join(where)}
            ORDER BY c.experience_years DESC NULLS LAST, c.candidate_id
            LIMIT %s""",
        params + [top_k],
    )
    return [(r["candidate_id"], None) for r in cursor.fetchall()], "filters"


def _fetch_details(cursor, ranked):
    """Full candidate records for the winners, in ranked order."""
    ids = [candidate_id for candidate_id, _ in ranked]
    if not ids:
        return []
    cursor.execute(
        """SELECT c.candidate_id, c.name, c.email, c.phone, c.education, c.experience_years,
                  COALESCE(array_agg(s.skill ORDER BY s.skill)
                           FILTER (WHERE s.skill IS NOT NULL), '{}') AS skills
           FROM candidates c
           LEFT JOIN candidate_skills s ON s.candidate_id = c.candidate_id
           WHERE c.candidate_id = ANY(%s)
           GROUP BY c.candidate_id""",
        (ids,),
    )
    details = {row["candidate_id"]: dict(row) for row in cursor.fetchall()}

    results = []
    for candidate_id, similarity in ranked:
        record = details[candidate_id]
        record["similarity"] = round(similarity * 100, 1) if similarity is not None else None
        record["source"] = "database"
        results.append(record)
    return results


def search_candidates_db(query, top_k=10, min_years=None, min_similarity=None):
    """Search the candidates stored in PostgreSQL.

    Returns {"matches": [...], "filters": {...}, "source": "llm"|"regex"|None,
             "mode": "vector"|"keyword"|"filters"|"none", "relaxed": bool}

    min_years is an extra floor from the UI's "minimum experience" box; the
    larger of it and any years rule in the text is used.
    """
    query = (query or "").strip()
    if not query:
        return {"matches": [], "filters": {}, "source": None, "mode": "none", "relaxed": False}

    min_similarity = DB_SEARCH_MIN_SIMILARITY if min_similarity is None else min_similarity
    filters, source = extract_filters(query)
    if min_years:
        filters["min_years"] = max(int(min_years), filters.get("min_years", 0))

    relaxed = False
    with db_session() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            ranked, mode = _rank_ids(cursor, filters, top_k, min_similarity)

            if not ranked and filters.get("skills"):
                # Nobody has every must-have skill: fall back to meaning only,
                # keeping the skills as part of the text, and tell the user.
                soft = {k: v for k, v in filters.items() if k != "skills"}
                soft["semantic_text"] = (filters.get("semantic_text", "") + " " + " ".join(filters["skills"])).strip()
                ranked, mode = _rank_ids(cursor, soft, top_k, min_similarity)
                relaxed = True

            matches = _fetch_details(cursor, ranked)

    return {"matches": matches, "filters": filters, "source": source, "mode": mode, "relaxed": relaxed}
