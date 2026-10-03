"""
Create (or re-create) candidate embeddings for pgvector search.

Why this exists: candidates saved through the app already get an embedding, but
the bulk ingest scripts (ingest_relational_54k.py, ingest_livecareer.py,
ingest_synthetic.py) COPY rows straight into PostgreSQL and do not embed them.
Run this afterwards so those candidates can be found by meaning.

    python -m scripts.backfill_embeddings              # only rows with no embedding yet
    python -m scripts.backfill_embeddings --rebuild    # re-embed everyone (after changing the model)
    python -m scripts.backfill_embeddings --limit 1000 --batch-size 128

Requires USE_DATABASE-style setup: DATABASE_URL, the pgvector extension and
sql/migrations/001_pgvector_candidate_search.sql applied.
"""

import argparse
import time

from psycopg2.extras import RealDictCursor, execute_values

from src.config.db import db_session
from src.config.settings import EMBEDDING_MODEL_NAME
from src.matching.embedding_matcher import embed_texts, embeddings_available
from src.retrieval.profile_text import build_profile_text

FETCH_SQL = """
    SELECT c.candidate_id, c.education, c.experience_years, c.category,
           COALESCE(array_agg(s.skill ORDER BY s.skill) FILTER (WHERE s.skill IS NOT NULL), '{}') AS skills
    FROM candidates c
    LEFT JOIN candidate_skills s ON s.candidate_id = c.candidate_id
    WHERE c.candidate_id > %s {only_missing}
    GROUP BY c.candidate_id
    ORDER BY c.candidate_id
    LIMIT %s
"""


def backfill(batch_size=256, limit=None, rebuild=False):
    if not embeddings_available():
        raise SystemExit("sentence-transformers is not available; install it first "
                         "(pip install sentence-transformers).")

    only_missing = "" if rebuild else "AND c.embedding IS NULL"
    done, last_id, started = 0, 0, time.time()

    with db_session() as conn:
        while limit is None or done < limit:
            size = batch_size if limit is None else min(batch_size, limit - done)
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(FETCH_SQL.replace("{only_missing}", only_missing), (last_id, size))
                rows = cursor.fetchall()
            if not rows:
                break

            last_id = rows[-1]["candidate_id"]
            profiles = [(row["candidate_id"], build_profile_text(row)) for row in rows]
            profiles = [(cid, text) for cid, text in profiles if text]   # never embed empty text
            if profiles:
                vectors = embed_texts([text for _, text in profiles])
                with conn.cursor() as cursor:
                    _update(cursor, profiles, vectors)
            conn.commit()
            done += len(rows)
            print(f"  embedded {done} candidates ({time.time() - started:.1f}s)")

    print(f"Done. {done} candidates processed with {EMBEDDING_MODEL_NAME}.")
    return done


def _update(cursor, profiles, vectors):
    execute_values(
        cursor,
        """UPDATE candidates AS c
           SET profile_text = v.profile_text, embedding = v.embedding::vector,
               embedding_model = v.model
           FROM (VALUES %s) AS v(candidate_id, profile_text, embedding, model)
           WHERE c.candidate_id = v.candidate_id""",
        [(cid, text, vec, EMBEDDING_MODEL_NAME) for (cid, text), vec in zip(profiles, vectors)],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--limit", type=int, default=None, help="stop after this many candidates")
    parser.add_argument("--rebuild", action="store_true", help="re-embed every candidate, not just missing ones")
    args = parser.parse_args()
    backfill(batch_size=args.batch_size, limit=args.limit, rebuild=args.rebuild)
