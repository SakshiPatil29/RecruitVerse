-- RecruitVerse ATS schema (optional — only used when USE_DATABASE=true).
--
-- The app runs fully in session-memory without any database. These tables
-- back optional persistence and the dataset-ingestion scripts in scripts/.

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id      SERIAL PRIMARY KEY,
    name              TEXT,
    email             TEXT,
    phone             TEXT,
    education         TEXT,
    experience_years  INTEGER,
    -- provenance for bulk-imported dataset rows
    source            TEXT,
    external_id       TEXT,
    category          TEXT,
    city              TEXT,
    created_at        TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS candidate_skills (
    id            SERIAL PRIMARY KEY,
    candidate_id  INTEGER REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    skill         TEXT
);

CREATE TABLE IF NOT EXISTS candidate_education (
    id            SERIAL PRIMARY KEY,
    candidate_id  INTEGER REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    institution   TEXT,
    program       TEXT,
    start_date    TEXT,
    location      TEXT
);

CREATE TABLE IF NOT EXISTS candidate_experience (
    id            SERIAL PRIMARY KEY,
    candidate_id  INTEGER REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    title         TEXT,
    firm          TEXT,
    start_date    TEXT,
    end_date      TEXT,
    location      TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id            SERIAL PRIMARY KEY,
    job_title         TEXT,
    education         TEXT,
    experience_years  INTEGER,
    created_at        TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS job_skills (
    id       SERIAL PRIMARY KEY,
    job_id   INTEGER REFERENCES jobs(job_id) ON DELETE CASCADE,
    skill    TEXT
);

-- Performance indexes for skill/candidate search over large imported datasets.
CREATE UNIQUE INDEX IF NOT EXISTS idx_candidates_source_external_id
    ON candidates(source, external_id) WHERE source IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_candidate_skills_skill_lower ON candidate_skills (LOWER(skill));
CREATE INDEX IF NOT EXISTS idx_candidate_skills_candidate_id ON candidate_skills (candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_education_candidate_id ON candidate_education(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_experience_candidate_id ON candidate_experience(candidate_id);

-- ---------------------------------------------------------------------------
-- Candidate Search (PostgreSQL + pgvector). Same statements as
-- sql/migrations/001_pgvector_candidate_search.sql. Kept at the END of the
-- file so the tables above are still created if pgvector is not installed.
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE candidates
    ADD COLUMN IF NOT EXISTS profile_text    TEXT,
    ADD COLUMN IF NOT EXISTS embedding       vector(384),   -- all-MiniLM-L6-v2
    ADD COLUMN IF NOT EXISTS embedding_model TEXT;

CREATE INDEX IF NOT EXISTS idx_candidates_embedding
    ON candidates USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_candidates_experience_years ON candidates (experience_years);
CREATE INDEX IF NOT EXISTS idx_candidates_email_lower ON candidates (LOWER(email));
