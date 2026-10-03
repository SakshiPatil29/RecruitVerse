# RecruitVerse ATS

An AI-powered **Resume Screening & Candidate Ranking System** that simulates a recruiter’s hiring workflow — from job description and resume parsing to semantic matching, candidate ranking, explainable scoring, and AI-assisted candidate analysis.

RecruitVerse combines **deterministic scoring, NLP-based semantic matching, PostgreSQL + pgvector search, and optional LLM-powered insights** to provide an explainable ATS workflow.

---

## 🚀 Key Features

* 📄 **Job Description Parsing** — Extract required/preferred skills, experience, education, and certifications from PDF, DOCX, or TXT files.
* 📑 **Resume Parsing** — Upload and parse multiple candidate resumes.
* 🎯 **Deterministic Candidate Scoring** — Transparent score based on skills, semantic similarity, and experience.
* 🧠 **Semantic Matching** — Uses Sentence-Transformers embeddings to measure meaning-based similarity between resumes and job descriptions.
* 📊 **Candidate Ranking** — Generates a ranked shortlist with score breakdowns and analytics.
* 🔍 **Natural-Language Candidate Search** — Search candidates using queries such as:

  * `Python developer with 3+ years experience`
  * `Candidates with Hadoop and ML experience`
  * `Backend developer with streaming experience`
* 🗄️ **PostgreSQL + pgvector Search** — Supports exact filtering and vector similarity search over candidate profiles.
* 🤖 **AI Insights** — Optional Groq-powered summaries, strengths/weaknesses, hiring recommendations, interview questions, resume tips, and JD summaries.
* 💡 **Explainable Results** — Shows matched, missing, and additional skills along with score explanations.
* 🔄 **LLM Fallbacks** — Core functionality remains usable even when an LLM API key is unavailable.
* 🐳 **Docker Support** — Run the Streamlit application, FastAPI API, and PostgreSQL database using Docker Compose.
* 🧪 **Automated Testing** — Includes deterministic pipeline, query-understanding, and PostgreSQL/pgvector tests.

---

## 🛠️ Tech Stack

| Category         | Technologies                 |
| ---------------- | ---------------------------- |
| Language         | Python                       |
| UI               | Streamlit                    |
| NLP              | Sentence-Transformers, spaCy |
| Embeddings       | `all-MiniLM-L6-v2`           |
| AI / LLM         | Groq                         |
| Database         | PostgreSQL                   |
| Vector Search    | pgvector, HNSW               |
| API              | FastAPI                      |
| Data Processing  | Pandas                       |
| Containerization | Docker, Docker Compose       |
| Testing          | Pytest                       |
| Version Control  | Git, GitHub                  |

---

## 🔄 Application Workflow

```text
Job Description
       ↓
Resume Upload
       ↓
Resume / JD Parsing
       ↓
Skill Extraction
       ↓
Semantic Matching
       ↓
Candidate Scoring
       ↓
Candidate Ranking
       ↓
Candidate Analysis
       ↓
AI Insights / Interview Questions
```

---

## 📊 How Candidate Scoring Works

The **match score is deterministic** and does not depend on the LLM.

| Component            | Weight | Description                                              |
| -------------------- | :----: | -------------------------------------------------------- |
| Skill Match          |   50%  | Required-skill coverage from the job description         |
| Semantic Similarity  |   30%  | Embedding similarity between the full resume and full JD |
| Experience Relevance |   20%  | Candidate experience compared with required experience   |

### Important Design Decision

**Groq is never used to calculate the candidate score or ranking.**

Groq is used only for narrative features such as:

* Candidate summaries
* Strengths and weaknesses
* Hiring recommendations
* Interview questions
* Resume improvement tips
* Job description summaries

If `GROQ_API_KEY` is unavailable or an LLM call fails, these features fall back to deterministic rule-based responses.

This keeps the core screening and ranking process **transparent, reproducible, and explainable**.

---

# 🔎 Candidate Search

RecruitVerse supports natural-language candidate search through three possible sources:

```text
                         Candidate Search
                               │
             ┌─────────────────┼─────────────────┐
             ↓                 ↓                 ↓
       Uploaded Batch    Knowledge Base    PostgreSQL
                                             + pgvector
```

When PostgreSQL search is enabled, a recruiter can enter a natural-language query such as:

```text
Python developer with 3+ years of experience and ML knowledge
```

The search pipeline is:

```text
Recruiter Query
      ↓
Query Understanding
      ↓
Extract structured filters
      ↓
Exact rules ───────────────→ SQL WHERE conditions
      │
      ↓
Semantic description
      ↓
Sentence-Transformer embedding
      ↓
pgvector similarity search
      ↓
Candidate details
      ↓
Ranked results
```

### Example

For:

```text
Python developer with 3+ years of experience and ML knowledge
```

the system can separate:

```text
Experience:
3+ years

Required skills:
Python
ML

Semantic requirement:
developer / relevant experience
```

The exact requirements are handled using SQL filters, while the descriptive part is handled using vector similarity.

---

## 🧠 PostgreSQL + pgvector Architecture

When `USE_DATABASE=true`, candidate profiles are stored in PostgreSQL.

```text
Resume
   ↓
Resume Parser
   ↓
Structured JSON
   ↓
Candidate Loader
   ↓
PostgreSQL
   │
   ├── candidates
   ├── candidate_skills
   ├── education
   ├── experience
   └── embedding vector(384)
```

Candidate search:

```text
Natural-language query
        ↓
Query Understanding
        ↓
Parameterized SQL
        ↓
Exact filtering
        +
pgvector similarity
        ↓
Candidate Results
```

The embedding is generated using the same Sentence-Transformer model used for semantic matching.

The PostgreSQL vector column uses:

```text
vector(384)
```

and vector similarity is accelerated using an **HNSW index**.

### Security

The system uses **parameterized SQL queries** rather than dynamically constructing SQL from user input.

The LLM does **not** generate SQL.

Groq only returns a small structured JSON representation of the user's search intent, which is validated before being used by the application.

---

## 📄 Supported Candidate Search Sources

### 1. Uploaded Batch

Search candidates uploaded during the current screening session.

### 2. Knowledge Base

Search a larger backend corpus containing candidate/resume datasets.

### 3. PostgreSQL + pgvector

Search structured candidate profiles stored in PostgreSQL using:

* Exact SQL filters
* Skill filters
* Experience filters
* Vector similarity
* Candidate metadata

---

# 🤖 AI Features

Groq is used as an optional enhancement layer rather than as the core scoring engine.

AI-powered features include:

* Candidate summary
* Strengths and weaknesses
* Hiring recommendation
* Interview question generation
* Resume improvement suggestions
* Job description summary

The application remains functional without Groq because deterministic fallback logic is implemented.

---

# 📱 Application Pages

RecruitVerse contains eight main pages:

### Dashboard

Provides an overview of the current screening session and quick actions.

### Job Description

Upload or paste a JD and extract:

* Required skills
* Preferred skills
* Experience
* Education
* Certifications

### Resume Upload

Upload multiple candidate resumes and view parsing status.

### Candidate Ranking

Displays:

* Ranked candidates
* Overall score
* Skill score
* Semantic similarity
* Experience score
* Charts and analytics

### Candidate Details

Displays:

* Candidate profile
* Matched skills
* Missing skills
* Additional skills
* Score explanation
* AI-generated insights

### Candidate Search

Supports natural-language semantic candidate search across:

* Uploaded candidates
* Knowledge-base candidates
* PostgreSQL candidates

### AI Insights

Provides:

* JD summaries
* Candidate summaries
* Strengths and weaknesses
* Interview questions
* Hiring insights

### Settings

Provides configuration for:

* Embedding model
* Scoring weights
* Groq status
* Knowledge-base indexing

---

# 🏗️ Project Structure

```text
RecruitVerse/
│
├── app.py
├── README.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── .env.example
├── .gitignore
│
├── src/
│   ├── parser/
│   │   ├── resume parsing
│   │   └── JD parsing
│   │
│   ├── matching/
│   │   ├── embedding_matcher
│   │   └── skill_matcher
│   │
│   ├── ranking/
│   │   ├── scoring_engine
│   │   ├── candidate_ranker
│   │   └── analytics
│   │
│   ├── explainability/
│   │   └── deterministic score explanations
│   │
│   ├── ai/
│   │   ├── groq_client
│   │   └── insights
│   │
│   ├── pipeline/
│   │   └── screening_pipeline
│   │
│   ├── knowledge_base/
│   │   ├── dataset loaders
│   │   └── vector search
│   │
│   ├── retrieval/
│   │   ├── query_understanding
│   │   └── db_search
│   │
│   ├── database/
│   │   └── load_candidates
│   │
│   ├── ui/
│   │   ├── pages/
│   │   ├── state.py
│   │   └── theme.py
│   │
│   └── api/
│       └── FastAPI routes
│
├── scripts/
│   └── optional PostgreSQL ingestion scripts
│
├── sql/
│   ├── schema.sql
│   └── migrations/
│
├── docs/
│   └── candidate search documentation
│
├── tests/
│   ├── test_pipeline.py
│   ├── test_query_understanding.py
│   └── test_db_search.py
│
└── screenshots/
```

---

# ⚙️ Quick Start

## Local Setup

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

Activate it on Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit application:

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

The first run downloads the Sentence-Transformer embedding model.

---

# 🐳 Docker Setup

Start the Streamlit application:

```bash
docker compose up app
```

Start the FastAPI service:

```bash
docker compose up api
```

Start PostgreSQL:

```bash
docker compose up -d db
```

---

# 🔐 Optional Groq Configuration

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Then configure:

```text
GROQ_API_KEY=your_api_key
```

You can optionally configure:

```text
GROQ_MODEL=your_model
```

The application does not require Groq for deterministic candidate scoring and ranking.

---

# 🗄️ PostgreSQL + pgvector Setup

Start PostgreSQL:

```bash
docker compose up -d db
```

Initialize the database:

```bash
psql "$DATABASE_URL" -f sql/schema.sql
```

For an existing database, use:

```bash
psql "$DATABASE_URL" -f sql/migrations/001_pgvector_candidate_search.sql
```

Enable database mode in `.env`:

```text
USE_DATABASE=true
```

Load candidates:

```bash
python -m src.database.load_candidates
```

After bulk ingestion, generate missing embeddings:

```bash
python -m scripts.backfill_embeddings
```

---

# 📚 Knowledge Base

The backend knowledge base can contain three datasets:

```text
data/
├── imports/
│   └── relational_54k/
│
└── raw_resumes/
    ├── real/
    └── synthetic/
```

These datasets are intentionally not bundled with the repository because of their size and dataset distribution considerations.

After placing the datasets in the expected directories, build the knowledge-base index:

```bash
python -m src.knowledge_base.dataset_loader
```

Alternatively, use the **Build Knowledge Base Index** option from the Settings page.

---

# 🧪 Testing

Run the deterministic pipeline tests:

```bash
pytest tests/test_pipeline.py
```

Run the complete test suite:

```bash
pytest
```

PostgreSQL tests are skipped when a database is unavailable.

To run the PostgreSQL + pgvector tests:

```bash
TEST_DATABASE_ADMIN_URL=postgresql://postgres:postgres@localhost:5432/postgres pytest tests/test_db_search.py
```

---

# 🔒 Security Considerations

* API keys are stored in `.env` and excluded using `.gitignore`.
* SQL queries use parameterized statements.
* User input is not directly converted into SQL.
* The LLM does not generate executable SQL.
* LLM output is validated before being used by the application.
* Candidate scoring does not depend on LLM output.

---

# 🎯 Design Highlights

### Deterministic scoring

The core candidate score is reproducible and explainable.

### Semantic matching

Sentence-Transformers capture meaning beyond simple keyword matching.

### Hybrid search

Candidate Search combines:

```text
Exact filtering + Semantic similarity
```

This allows queries to contain both structured requirements and descriptive intent.

### LLM as an enhancement layer

The LLM is used for explanation and assistance rather than deciding the numerical candidate score.

### Modular architecture

Parsing, matching, ranking, retrieval, database, AI, UI, and API components are separated into independent modules.

---

# 🔮 Future Improvements

* Add recruiter authentication and role-based access control
* Add asynchronous resume processing for large batches
* Add richer candidate analytics
* Add configurable ranking strategies
* Add model evaluation dashboards
* Add production deployment configuration
* Add observability and application monitoring

---

## 👩‍💻 Author

**Sakshi Patil**

RecruitVerse was developed as an end-to-end project to explore **NLP, semantic search, vector databases, PostgreSQL, AI-assisted recruitment workflows, and explainable candidate ranking**.
