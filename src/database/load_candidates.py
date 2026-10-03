"""Store parsed candidates in PostgreSQL (only used when USE_DATABASE=true).

Each candidate is written to `candidates` + `candidate_skills`, together with a
short profile text and its embedding (a 384-number vector from
all-MiniLM-L6-v2), so the candidate can be found by meaning with pgvector.

Loading is safe to repeat: a candidate with the same e-mail address is updated
instead of being inserted again.
"""

import json
import logging
import os

from psycopg2.extras import execute_values

from src.config.db import db_session
from src.config.settings import EMBEDDING_MODEL_NAME
from src.retrieval.profile_text import build_profile_text, canonical_skills

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARSED_JSON_DIR = os.path.join(BASE_DIR, "data", "parsed_resumes", "parsed_json")


def _embed_profile(text):
    """Embedding for a profile text, or None when it cannot be made (empty
    text, or sentence-transformers not available). A candidate without an
    embedding is still stored and can be filled in later by
    scripts/backfill_embeddings.py."""
    if not text:
        return None
    try:
        from src.matching.embedding_matcher import embed_text, embeddings_available

        if not embeddings_available():
            return None
        return embed_text(text)
    except Exception as exc:
        logger.warning("Could not embed candidate profile (%s); storing without a vector.", exc)
        return None


def _years(value):
    """experience_years column is an integer; resumes can give 2.5, "Not
    Specified" or nothing. Unknown stays NULL instead of a made-up 0."""
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _find_candidate_id(cursor, email):
    if not email:
        return None
    cursor.execute(
        "SELECT candidate_id FROM candidates WHERE LOWER(email) = LOWER(%s) ORDER BY candidate_id LIMIT 1",
        (email,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def insert_candidate(cursor, candidate):
    """Insert a parsed candidate, or update the existing one with the same
    e-mail. Returns candidate_id."""
    skills = canonical_skills(candidate.get("skills"))
    profile = build_profile_text({**candidate, "skills": skills})
    vector = _embed_profile(profile)
    model = EMBEDDING_MODEL_NAME if vector is not None else None

    candidate_id = _find_candidate_id(cursor, candidate.get("email"))
    if candidate_id is None:
        cursor.execute(
            """
            INSERT INTO candidates(
                name, email, phone, education, experience_years,
                profile_text, embedding, embedding_model
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING candidate_id
            """,
            (
                candidate.get("name"),
                candidate.get("email"),
                candidate.get("phone"),
                candidate.get("education"),
                _years(candidate.get("experience_years")),
                profile or None,
                vector,
                model,
            ),
        )
        candidate_id = cursor.fetchone()[0]
    else:
        cursor.execute(
            """
            UPDATE candidates
            SET name = %s, phone = %s, education = %s, experience_years = %s,
                profile_text = %s, embedding = %s, embedding_model = %s
            WHERE candidate_id = %s
            """,
            (
                candidate.get("name"),
                candidate.get("phone"),
                candidate.get("education"),
                _years(candidate.get("experience_years")),
                profile or None,
                vector,
                model,
                candidate_id,
            ),
        )
        cursor.execute("DELETE FROM candidate_skills WHERE candidate_id = %s", (candidate_id,))

    insert_skills(cursor, candidate_id, skills)
    return candidate_id


def insert_skills(cursor, candidate_id, skills):
    skills = canonical_skills(skills)
    if skills:
        execute_values(
            cursor,
            "INSERT INTO candidate_skills(candidate_id, skill) VALUES %s",
            [(candidate_id, skill) for skill in skills],
        )


def process_all_json(input_folder=PARSED_JSON_DIR):
    """Load every parsed candidate JSON file into the candidates and
    candidate_skills tables. A file that fails is skipped (and logged) without
    losing the others. Returns the number of candidates stored."""

    count = 0
    with db_session() as conn:
        cursor = conn.cursor()
        try:
            if os.path.isdir(input_folder):
                for file in sorted(os.listdir(input_folder)):
                    if not file.endswith(".json"):
                        continue
                    file_path = os.path.join(input_folder, file)
                    cursor.execute("SAVEPOINT one_candidate")
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            candidate = json.load(f)
                        insert_candidate(cursor, candidate)
                        cursor.execute("RELEASE SAVEPOINT one_candidate")
                        count += 1
                    except Exception as exc:
                        cursor.execute("ROLLBACK TO SAVEPOINT one_candidate")
                        logger.warning("Skipped %s: %s", file, exc)
        finally:
            cursor.close()
    return count


def persist_parsed_resumes(resumes):
    """Save resumes parsed in the UI. Never raises, so a database problem
    cannot break the upload page. Returns {"stored": int, "error": str | None}."""
    stored = 0
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            try:
                for resume in resumes:
                    insert_candidate(cursor, resume)
                    stored += 1
            finally:
                cursor.close()
        return {"stored": stored, "error": None}
    except Exception as exc:
        logger.warning("Could not save resumes to PostgreSQL: %s", exc)
        return {"stored": 0, "error": str(exc)}


if __name__ == "__main__":
    total = process_all_json()
    print(f"Total Candidates Stored: {total}")
