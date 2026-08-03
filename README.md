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

**Ollama is never used for scoring or ranking.** It powers only the narrative
features (summaries, strengths/weaknesses, hiring recommendation, interview
questions, resume tips, JD summary). If Ollama isn't running, every one of
those features falls back to a deterministic rule-based version, so the app
stays fully usable with no LLM at all.

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

### Optional: Ollama for AI features

```bash
ollama serve
ollama pull llama3
```
Set `OLLAMA_HOST` / `OLLAMA_MODEL` if they differ from the defaults.

---

## The eight pages

- **Dashboard** — session overview and quick actions
- **Job Description** — paste or upload (PDF/DOCX/TXT); extracts required vs preferred skills, experience, education, certifications
- **Resume Upload** — drag-and-drop multiple resumes with parse status
- **Candidate Ranking** — sortable ranked table with score breakdown + charts
- **Candidate Details** — full profile, matched/missing/additional skills, ✓/✗ score explanation, and on-demand AI insights
- **Candidate Search** — natural-language semantic search
- **AI Insights** — JD summary and top-candidate AI helpers
- **Settings** — model/weights/Ollama status; build the knowledge-base index

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

## Project layout

```
app.py                     Streamlit entrypoint (routing only)
src/
  parser/                  file extraction, resume & JD parsing
  matching/                embedding_matcher (semantic), skill_matcher
  ranking/                 scoring_engine, candidate_ranker, analytics
  explainability/          deterministic ✓/✗ score explanations
  ai/                      ollama_client + insights (with fallbacks)
  pipeline/                screening_pipeline (parse→match→score→rank)
  knowledge_base/          dataset loaders + vector search index
  retrieval/               unified candidate search
  ui/                      theme, state, and the 8 pages
  api/                     FastAPI routes over the same pipeline
scripts/                   optional dataset ingestion into Postgres
sql/schema.sql             optional persistence schema
tests/test_pipeline.py     deterministic core tests
```

## Tests

```bash
pytest tests/test_pipeline.py
```
