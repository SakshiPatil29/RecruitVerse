import json
import os

from src.config.db import get_connection

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARSED_JSON_DIR = os.path.join(BASE_DIR, "data", "parsed_resumes", "parsed_json")


def insert_candidate(cursor, candidate):
    cursor.execute(
        """
        INSERT INTO candidates(
            name, email, phone, education, experience_years
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING candidate_id
        """,
        (
            candidate.get("name"),
            candidate.get("email"),
            candidate.get("phone"),
            candidate.get("education"),
            candidate.get("experience_years"),
        ),
    )

    candidate_id = cursor.fetchone()[0]
    insert_skills(cursor, candidate_id, candidate.get("skills", []))
    return candidate_id


def insert_skills(cursor, candidate_id, skills):
    for skill in skills:
        cursor.execute(
            "INSERT INTO candidate_skills(candidate_id, skill) VALUES (%s, %s)",
            (candidate_id, skill),
        )


def process_all_json(input_folder=PARSED_JSON_DIR):
    """Load every parsed candidate JSON file into the candidates and
    candidate_skills tables. Returns the number of candidates inserted."""

    conn = get_connection()
    cursor = conn.cursor()
    count = 0

    try:
        if os.path.isdir(input_folder):
            for file in os.listdir(input_folder):
                if file.endswith(".json"):
                    file_path = os.path.join(input_folder, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        candidate = json.load(f)

                    insert_candidate(cursor, candidate)
                    count += 1

        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return count


if __name__ == "__main__":
    total = process_all_json()
    print(f"Total Candidates Inserted: {total}")
