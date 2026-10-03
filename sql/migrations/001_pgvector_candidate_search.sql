-- Candidate Search: PostgreSQL + pgvector
--
-- Run once on an EXISTING recruitverse database (fresh installs get the same
-- statements from the bottom of sql/schema.sql). Safe to run more than once.
--
--   psql "$DATABASE_URL" -f sql/migrations/001_pgvector_candidate_search.sql
--
-- Needs the pgvector extension installed on the server. The docker-compose
-- "db" service uses the pgvector/pgvector:pg16 image, which includes it.

CREATE EXTENSION IF NOT EXISTS vector;

-- One short text per candidate is embedded (skills, education, experience),
-- not the whole resume. all-MiniLM-L6-v2 produces 384 numbers, so the column
-- is vector(384). If EMBEDDING_MODEL_NAME changes to a model with another
-- size, change this and re-embed everything (scripts/backfill_embeddings.py --rebuild).
ALTER TABLE candidates
    ADD COLUMN IF NOT EXISTS profile_text    TEXT,
    ADD COLUMN IF NOT EXISTS embedding       vector(384),
    ADD COLUMN IF NOT EXISTS embedding_model TEXT;

-- Approximate nearest-neighbour index for cosine distance (the <=> operator).
CREATE INDEX IF NOT EXISTS idx_candidates_embedding
    ON candidates USING hnsw (embedding vector_cosine_ops);

-- Helpers for the structured filters and for upsert-by-email.
CREATE INDEX IF NOT EXISTS idx_candidates_experience_years ON candidates (experience_years);
CREATE INDEX IF NOT EXISTS idx_candidates_email_lower ON candidates (LOWER(email));
