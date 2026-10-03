"""
Ingests the Livecareer "Resume Dataset" (ID, Resume_str, Resume_html,
Category) into candidates / candidate_skills, using the project's existing
skill_extractor and education/experience heuristics on the real resume text.

NOTE: this public dataset has no real names — resumes start directly with a
role/title line. `name` will reflect whatever line the extractor picks up
as a result; it's stored with source='livecareer' so this is identifiable.

Usage:
    python -m scripts.ingest_livecareer [--csv data/imports/livecareer_resumes.csv] [--limit N]
"""

import argparse
import io
import time

import pandas as pd

from src.config.db import get_connection
from src.matching.skill_extractor import extract_skills
from src.parser.resume_parser import extract_education, extract_experience


def copy_df(cursor, df, table, columns):
    if df.empty:
        return
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, columns=columns)
    buf.seek(0)
    cursor.copy_expert(
        f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv, NULL '')",
        buf,
    )


def run(csv_path, limit=None):
    t0 = time.time()

    df = pd.read_csv(csv_path)
    if limit:
        df = df.head(limit)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COALESCE(MAX(candidate_id), 0) FROM candidates")
        start_id = cursor.fetchone()[0] + 1

        rows = []
        skill_rows = []
        for i, row in enumerate(df.itertuples(index=False)):
            candidate_id = start_id + i
            text = str(row.Resume_str)
            rows.append({
                "candidate_id": candidate_id,
                "name": f"{row.Category.title().replace('-', ' ')} Candidate #{row.ID}",
                "email": None,
                "phone": None,
                "education": extract_education(text),
                "experience_years": extract_experience(text),
                "source": "livecareer",
                "external_id": str(row.ID),
                "category": row.Category,
            })
            for skill in extract_skills(text):
                skill_rows.append({"candidate_id": candidate_id, "skill": skill})

        candidates_df = pd.DataFrame(rows)
        copy_df(cursor, candidates_df, "candidates",
                ["candidate_id", "name", "email", "phone", "education",
                 "experience_years", "source", "external_id", "category"])
        print(f"  candidates: {len(candidates_df)} rows in {time.time() - t0:.1f}s")

        skills_df = pd.DataFrame(skill_rows)
        copy_df(cursor, skills_df, "candidate_skills", ["candidate_id", "skill"])
        print(f"  candidate_skills: {len(skills_df)} rows in {time.time() - t0:.1f}s")

        cursor.execute(
            "SELECT setval('candidates_candidate_id_seq', (SELECT MAX(candidate_id) FROM candidates))"
        )

        conn.commit()
        print(f"Done in {time.time() - t0:.1f}s — {len(candidates_df)} candidates loaded (source=livecareer)")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/imports/livecareer_resumes.csv")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    run(args.csv, args.limit)
