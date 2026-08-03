import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/recruitverse"


def get_connection():
    """Return a new psycopg2 connection using DATABASE_URL from the
    environment (see .env.example). Falls back to a sane local default
    so the project still runs out of the box in local dev."""

    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    return psycopg2.connect(database_url)


def get_cursor(connection):
    return connection.cursor()
