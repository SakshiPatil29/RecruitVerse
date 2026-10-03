import os
from contextlib import contextmanager

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


def pgvector_enabled(conn):
    """True if the pgvector extension exists in the connected database."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        return cursor.fetchone() is not None


@contextmanager
def db_session():
    """Open a connection for one unit of work.

        with db_session() as conn:
            ...

    Commits if the block finishes, rolls back if it raises, and always closes
    the connection. If pgvector is installed, its type is registered so numpy
    arrays can be sent to and read from vector columns.
    """
    conn = get_connection()
    try:
        if pgvector_enabled(conn):
            from pgvector.psycopg2 import register_vector

            register_vector(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
