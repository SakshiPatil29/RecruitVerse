"""
Refreshes the skill_usage summary table from candidate_skills.

This exists because /talent_insights and the Business Intelligence dashboard
page were either reading an empty skill_usage table, or live-aggregating
candidate_skills (2M+ rows) on every request. Run this after any bulk
candidate import so those pages stay fast and accurate.

Usage:
    python -m scripts.refresh_skill_usage
"""

from src.config.db import get_connection


def run():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE skill_usage")
        cursor.execute(
            """
            INSERT INTO skill_usage(skill_name, occurrences, recorded_date)
            SELECT skill, COUNT(*), CURRENT_DATE
            FROM candidate_skills
            WHERE skill IS NOT NULL
            GROUP BY skill
            """
        )
        cursor.execute("SELECT COUNT(*) FROM skill_usage")
        count = cursor.fetchone()[0]
        conn.commit()
        print(f"skill_usage refreshed: {count} distinct skills")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    run()
