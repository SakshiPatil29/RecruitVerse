import os
import subprocess
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/recruitverse"


def backup_database(output_file="backup.sql"):
    """Dump the RecruitVerse database to output_file using pg_dump,
    reading connection details from DATABASE_URL (see .env.example)."""

    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    parsed = urlparse(database_url)

    env = os.environ.copy()
    if parsed.password:
        env["PGPASSWORD"] = parsed.password

    cmd = [
        "pg_dump",
        "-h", parsed.hostname or "localhost",
        "-p", str(parsed.port or 5432),
        "-U", parsed.username or "postgres",
        parsed.path.lstrip("/"),
    ]

    with open(output_file, "w") as f:
        result = subprocess.run(cmd, stdout=f, env=env)

    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed with exit code {result.returncode}")

    return output_file


if __name__ == "__main__":
    path = backup_database()
    print(f"Database backed up to {path}")
