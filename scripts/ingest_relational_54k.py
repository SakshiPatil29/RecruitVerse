"""
Ingests the ~54,933-person normalized dataset (01_people.csv, 03_education.csv,
04_experience.csv, 05_person_skills.csv) into candidates / candidate_education /
candidate_experience / candidate_skills using bulk COPY.

NOTE on the "name" field: this public dataset anonymizes real names — the
`name` column in 01_people.csv is actually a role/title placeholder (e.g.
"Python Developer"), not a real person's name. It's stored as-is with
source='relational_54k' so it's always identifiable in the database.

Usage:
    python -m scripts.ingest_relational_54k [--dir data/imports/relational_54k] [--limit N]
"""

import argparse
import io
import re
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


def estimate_experience_years(exp_rows):
    """Best-effort: count distinct roles as a rough proxy when dates are too
    inconsistent to reliably parse (mixed formats, 'Present', blanks)."""
    years = set()
    for start in exp_rows:
        m = re.search(r"(19|20)\d{2}", str(start))
        if m:
            years.add(int(m.group()))
    if len(years) >= 2:
        return max(years) - min(years)
    return len(exp_rows)  # fallback: rough proxy


def run(data_dir, limit=None):
    t0 = time.time()

    people = pd.read_csv(f"{data_dir}/01_people.csv")
    education = pd.read_csv(f"{data_dir}/03_education.csv")
    experience = pd.read_csv(f"{data_dir}/04_experience.csv")
    skills = pd.read_csv(f"{data_dir}/05_person_skills.csv")

    if limit:
        people = people.head(limit)
        keep_ids = set(people["person_id"])
        education = education[education["person_id"].isin(keep_ids)]
        experience = experience[experience["person_id"].isin(keep_ids)]
        skills = skills[skills["person_id"].isin(keep_ids)]

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COALESCE(MAX(candidate_id), 0) FROM candidates")
        start_id = cursor.fetchone()[0] + 1

        # person_id -> new candidate_id mapping, assigned explicitly so we
        # don't need RETURNING (which COPY doesn't support)
        id_map = {pid: start_id + i for i, pid in enumerate(people["person_id"])}

        candidates_df = pd.DataFrame({
            "candidate_id": people["person_id"].map(id_map),
            "name": people["name"],
            "email": people["email"],
            "phone": people["phone"],
            "education": None,
            "experience_years": 0,
            "source": "relational_54k",
            "external_id": people["person_id"].astype(str),
        })
        copy_df(cursor, candidates_df, "candidates",
                ["candidate_id", "name", "email", "phone", "education",
                 "experience_years", "source", "external_id"])
        print(f"  candidates: {len(candidates_df)} rows in {time.time() - t0:.1f}s")

        edu_df = education.copy()
        edu_df["candidate_id"] = edu_df["person_id"].map(id_map)
        edu_df = edu_df.dropna(subset=["candidate_id"])
        edu_df["candidate_id"] = edu_df["candidate_id"].astype(int)
        copy_df(cursor, edu_df, "candidate_education",
                ["candidate_id", "institution", "program", "start_date", "location"])
        print(f"  candidate_education: {len(edu_df)} rows in {time.time() - t0:.1f}s")

        exp_df = experience.copy()
        exp_df["candidate_id"] = exp_df["person_id"].map(id_map)
        exp_df = exp_df.dropna(subset=["candidate_id"])
        exp_df["candidate_id"] = exp_df["candidate_id"].astype(int)
        copy_df(cursor, exp_df, "candidate_experience",
                ["candidate_id", "title", "firm", "start_date", "end_date", "location"])
        print(f"  candidate_experience: {len(exp_df)} rows in {time.time() - t0:.1f}s")

        # rough experience_years per candidate from their experience rows
        years_by_candidate = (
            exp_df.groupby("candidate_id")["start_date"]
            .apply(lambda s: estimate_experience_years(list(s)))
        )
        for cid, yrs in years_by_candidate.items():
            cursor.execute(
                "UPDATE candidates SET experience_years = %s WHERE candidate_id = %s",
                (int(yrs), int(cid)),
            )

        skills_df = skills.copy()
        skills_df["candidate_id"] = skills_df["person_id"].map(id_map)
        skills_df = skills_df.dropna(subset=["candidate_id"])
        skills_df["candidate_id"] = skills_df["candidate_id"].astype(int)
        skills_df = skills_df.rename(columns={"skill": "skill"})
        copy_df(cursor, skills_df, "candidate_skills", ["candidate_id", "skill"])
        print(f"  candidate_skills: {len(skills_df)} rows in {time.time() - t0:.1f}s")

        cursor.execute(
            "SELECT setval('candidates_candidate_id_seq', (SELECT MAX(candidate_id) FROM candidates))"
        )

        conn.commit()
        print(f"Done in {time.time() - t0:.1f}s — {len(candidates_df)} candidates loaded (source=relational_54k)")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="data/imports/relational_54k")
    parser.add_argument("--limit", type=int, default=None, help="Only load the first N people (for testing)")
    args = parser.parse_args()
    run(args.dir, args.limit)
