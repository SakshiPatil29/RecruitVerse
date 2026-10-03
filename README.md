# RecruitVerse ATS

An AI-powered **Resume Screening & Candidate Ranking System** that simulates
a recruiter's hiring workflow: upload a job description, upload a batch of
resumes, and get an explainable, ranked shortlist — with optional AI-generated
summaries, hiring recommendations, and interview questions.

This is a focused refactor of the original RecruitVerse project: the broad
HR-suite modules (workflow, governance, monitoring, MLOps, notifications,
talent intelligence, recommendations) were removed, and the resume-screening
core was rebuilt around **real semantic matching** and a clean ATS UI.

---

## The workflow

```
Job Description  →  Resume Upload  →  Parsing  →  Semantic Matching
                 →  Skill Extraction  →  Ranking  →  Candidate Analysis
                 →  Interview Questions  →  Hiring Recommendation
```

## How scoring works (and where AI does / doesn't touch it)

The **match score is deterministic** — computed from three components:

| Component            | Weight | Source                                        |
|----------------------|:------:|-----------------------------------------------|
| Skill match          |  50%   | JD required-skill coverage                     |
| Semantic similarity  |  30%   | Sentence-Transformers embeddings (full resume vs full JD) |
| Experience relevance |  20%   | Candidate years vs required years              |

**Groq is never used for scoring or ranking.** It powers only the narrative
features (summaries, strengths/weaknesses, hiring recommendation, interview
questions, resume tips, JD summary). If `GROQ_API_KEY` isn't set (or a call
fails), every one of those features falls back to a deterministic rule-based
version, so the app stays fully usable with no LLM at all.

---

## Quick start (local, no database, no Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. The first run downloads the embedding model
(~90 MB) once.

### With Docker

```bash
docker compose up app       # Streamlit UI on :8501
docker compose up api       # FastAPI on :8000 (optional)
```

### Optional: Groq for AI features

```bash
cp .env.example .env
# then edit .env and set GROQ_API_KEY=gsk_...  (get one at https://console.groq.com/keys)
```
Set `GROQ_MODEL` if you want a different current Groq model than the default.

---

## The eight pages

- **Dashboard** — session overview and quick actions
- **Job Description** — paste or upload (PDF/DOCX/TXT); extracts required vs preferred skills, experience, education, certifications
- **Resume Upload** — drag-and-drop multiple resumes with parse status
- **Candidate Ranking** — sortable ranked table with score breakdown + charts
- **Candidate Details** — full profile, matched/missing/additional skills, ✓/✗ score explanation, and on-demand AI insights
- **Candidate Search** — natural-language semantic search
- **AI Insights** — JD summary and top-candidate AI helpers
- **Settings** — model/weights/Groq status; build the knowledge-base index

---

## The datasets (backend knowledge base)

Three datasets act as a backend corpus for semantic **Candidate Search** —
recruiters never browse them directly:

- **Relational 54K** — `data/imports/relational_54k/` (people + skills CSVs)
- **Real / LiveCareer resumes** — `data/raw_resumes/real/dataset 1/Resume/Resume.csv`
- **Synthetic 10K** — `data/raw_resumes/synthetic/.../resumes_txt/*.txt`

Because these are large, they aren't bundled here — drop them into the folders
above (structure preserved), then build the search index:

```bash
python -m src.knowledge_base.dataset_loader
# or use the "Build knowledge base index" button on the Settings page
```

Optional bulk import into PostgreSQL (only with `USE_DATABASE=true`) is
available via `scripts/ingest_*.py`.

---

## Candidate search with PostgreSQL + pgvector

When `USE_DATABASE=true`, candidates are stored in PostgreSQL and the Candidate
Search page gets a third section, **From the candidate database**, next to the
uploaded batch and the knowledge base.

```
resume -> parser -> JSON -> src/database/load_candidates.py -> PostgreSQL
                                                                 candidates (+ embedding vector(384))
                                                                 candidate_skills / education / experience
recruiter text -> src/retrieval/query_understanding.py  (Groq JSON, regex fallback)
              -> src/retrieval/db_search.py             (ONE parameterised SQL statement)
                    exact rules  ("3+ years", must-have skills)  -> WHERE
                    meaning      ("backend developer, streaming") -> ORDER BY embedding <=> query_vector
              -> candidate details -> Streamlit
```

* Exact rules run as SQL; the descriptive part is embedded with the same
  all-MiniLM-L6-v2 model and ranked by cosine distance (pgvector, HNSW index).
* Groq only turns the search text into a small JSON of filters. Its reply is
  validated, it never writes SQL, and it never sees the database. Without a
  key (or if the reply is invalid) a regex parser does the same job.
* Loading is repeatable: a candidate with the same e-mail is updated, not duplicated.

Setup (details in [docs/CANDIDATE_SEARCH.md](docs/CANDIDATE_SEARCH.md)):

```bash
docker compose up -d db        # PostgreSQL 16 with the pgvector extension
psql "$DATABASE_URL" -f sql/schema.sql        # or sql/migrations/001_pgvector_candidate_search.sql on an existing database
# in .env:  USE_DATABASE=true
python -m src.database.load_candidates        # load the sample parsed resumes
python -m scripts.backfill_embeddings         # after bulk ingest scripts: embed rows that have no vector yet
```

---

## Project layout

```
app.py                     Streamlit entrypoint (routing only)
src/
  parser/                  file extraction, resume & JD parsing
  matching/                embedding_matcher (semantic), skill_matcher
  ranking/                 scoring_engine, candidate_ranker, analytics
  explainability/          deterministic ✓/✗ score explanations
  ai/                      groq_client + insights (with fallbacks)
  pipeline/                screening_pipeline (parse→match→score→rank)
  knowledge_base/          dataset loaders + vector search index
  retrieval/               unified candidate search (batch + knowledge base + PostgreSQL/pgvector)
  database/                load parsed candidates into PostgreSQL (with embeddings)
  ui/                      theme, state, and the 8 pages
  api/                     FastAPI routes over the same pipeline
scripts/                   optional dataset ingestion into Postgres
sql/schema.sql             optional persistence schema (incl. pgvector column + index)
sql/migrations/            upgrade an existing database for pgvector search
docs/                      module notes (candidate search)
tests/test_pipeline.py     deterministic core tests
tests/test_query_understanding.py   search-text parsing (no database needed)
tests/test_db_search.py    PostgreSQL + pgvector search (needs a database, see below)
```

## Tests

```bash
pytest tests/test_pipeline.py
pytest                                   # everything; PostgreSQL tests are skipped without a database

# PostgreSQL + pgvector tests (creates and drops a throw-away database)
TEST_DATABASE_ADMIN_URL=postgresql://postgres:postgres@localhost:5432/postgres pytest tests/test_db_search.py
```
