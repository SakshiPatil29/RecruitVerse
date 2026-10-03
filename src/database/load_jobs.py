import json
import os

from src.config.db import get_connection

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARSED_JD_DIR = os.path.join(BASE_DIR, "data", "parsed_job_descriptions")


def insert_job(cursor, job, job_title):
    cursor.execute(
        """
        INSERT INTO jobs(job_title, education, experience_years)
        VALUES (%s, %s, %s)
        RETURNING job_id
        """,
        (job_title, job.get("education"), job.get("experience_years")),
    )

    job_id = cursor.fetchone()[0]
    insert_job_skills(cursor, job_id, job.get("skills", []))
    return job_id


def insert_job_skills(cursor, job_id, skills):
    for skill in skills:
        cursor.execute(
            "INSERT INTO job_skills(job_id, skill) VALUES (%s, %s)",
            (job_id, skill),
        )


def process_all_jobs(input_folder=PARSED_JD_DIR):
    """Load every parsed job-description JSON file into the jobs and
    job_skills tables. Returns the number of jobs inserted."""

    conn = get_connection()
    cursor = conn.cursor()
    count = 0

    try:
        if os.path.isdir(input_folder):
            for file in os.listdir(input_folder):
                if file.endswith(".json"):
                    file_path = os.path.join(input_folder, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        job = json.load(f)

                    job_title = file.replace(".json", "")
                    insert_job(cursor, job, job_title)
                    count += 1

        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return count


if __name__ == "__main__":
    total = process_all_jobs()
    print(f"Total Jobs Inserted: {total}")
