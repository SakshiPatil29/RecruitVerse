"""
Ingests the 10,000-row synthetic RecruitVerse dataset (already clean,
structured CSV) into candidates / candidate_skills.

Usage:
    python -m scripts.ingest_synthetic [--csv data/imports/synthetic_resumes.csv] [--limit N]
"""

import argparse
import io
import time

import pandas as pd

from src.config.db import get_connection


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


def split_skills(value):
    if not isinstance(value, str) or not value.strip():
        return []
    return [s.strip() for s in value.split(";") if s.strip()]


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
            rows.append({
                "candidate_id": candidate_id,
                "name": row.name,
                "email": row.email,
                "phone": row.phone,
                "education": row.education,
                "experience_years": row.years_experience,
                "source": "synthetic",
                "external_id": row.candidate_id,
                "category": row.domain,
                "city": row.city,
            })
            skills = set(split_skills(row.primary_skills)) | set(split_skills(row.secondary_skills))
            for skill in skills:
                skill_rows.append({"candidate_id": candidate_id, "skill": skill})

        candidates_df = pd.DataFrame(rows)
        copy_df(cursor, candidates_df, "candidates",
                ["candidate_id", "name", "email", "phone", "education",
                 "experience_years", "source", "external_id", "category", "city"])
        print(f"  candidates: {len(candidates_df)} rows in {time.time() - t0:.1f}s")

        skills_df = pd.DataFrame(skill_rows)
        copy_df(cursor, skills_df, "candidate_skills", ["candidate_id", "skill"])
        print(f"  candidate_skills: {len(skills_df)} rows in {time.time() - t0:.1f}s")

        cursor.execute(
            "SELECT setval('candidates_candidate_id_seq', (SELECT MAX(candidate_id) FROM candidates))"
        )

        conn.commit()
        print(f"Done in {time.time() - t0:.1f}s — {len(candidates_df)} candidates loaded (source=synthetic)")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/imports/synthetic_resumes.csv")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    run(args.csv, args.limit)
