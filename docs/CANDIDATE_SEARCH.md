# Candidate Search module (PostgreSQL + pgvector)

This module stores parsed candidates in PostgreSQL and lets a recruiter find
them with natural-language queries. It is used only when `USE_DATABASE=true`;
the uploaded-batch search and the FAISS knowledge-base search work without it.

## Files

| File | Job |
|---|---|
| `sql/schema.sql`, `sql/migrations/001_pgvector_candidate_search.sql` | tables, `vector(384)` column, HNSW and helper indexes |
| `src/config/db.py` | `get_connection()` (unchanged) and `db_session()` (commit / rollback / close, registers pgvector) |
| `src/retrieval/profile_text.py` | skill normalisation (`ML` -> `machine learning`) and the short text that is embedded |
| `src/database/load_candidates.py` | parsed JSON -> PostgreSQL, update-or-insert by e-mail, embedding stored with the row |
| `src/retrieval/query_understanding.py` | recruiter text -> `{min_years, max_years, skills, semantic_text}` (Groq JSON, regex fallback) |
| `src/retrieval/db_search.py` | builds one parameterised SQL statement, runs it, fetches full details |
| `src/retrieval/search_candidates.py` | `semantic_search()` combines batch, knowledge base and database results |
| `src/ui/pages/candidate_search.py` | draws the "From the candidate database" section |
| `src/ui/pages/resume_upload.py` | saves freshly parsed resumes to PostgreSQL |
| `scripts/backfill_embeddings.py` | embeds rows that have no vector (bulk ingest, model change) |

## How one search runs

1. `semantic_search(query, ..., min_experience)` calls `search_candidates_db()`.
2. `extract_filters()` turns the text into filters. Example:
   `"Python and Kafka, 3+ years, backend developer"` ->
   `{"min_years": 3, "skills": ["python", "kafka"], "semantic_text": "backend developer"}`.
   Groq's reply is validated (known keys, types, ranges). On any problem the regex parser is used.
3. One SQL statement is built from the filters. Values are always parameters:
   * years -> `c.experience_years >= %s`
   * must-have skills -> `GROUP BY candidate_id HAVING COUNT(DISTINCT LOWER(skill)) = n`
   * meaning -> `ORDER BY c.embedding <=> %s` (cosine distance; `1 - distance` is the similarity shown)
4. A second query fetches name, e-mail, education, experience and all skills for the winners, in ranked order.

Modes reported to the UI: `vector` (meaning + filters), `filters` (only exact rules,
e.g. "3+ years"), `keyword` (embeddings unavailable: skill keywords only), `none`.

## Behaviour worth knowing

* **Same model everywhere.** Stored vectors and query vectors must come from the
  same model. If `EMBEDDING_MODEL_NAME` changes, update `vector(N)` and run
  `python -m scripts.backfill_embeddings --rebuild`. `embedding_model` records what made each vector.
* **Never embed empty text.** An all-zero vector gives a `NaN` distance, so empty profiles are stored without a vector.
* **Years rules and unknown experience.** `experience_years` is NULL when unknown, and
  `>= 3` excludes NULL. That is deliberate and tested.
* **Must-have skills are exact.** If nobody has all of them, the search relaxes to meaning-only and the page says so.
* **Approximate index.** HNSW is approximate. A very selective filter combined with it can return fewer
  than `top_k` rows; raise `hnsw.ef_search` or use an exact scan for tiny filtered sets.
* **Similarity is not a probability.** `38% match` is a scaled cosine value; `DB_SEARCH_MIN_SIMILARITY`
  (default 0.30, the same cut-off as the uploaded-batch search) should be tuned on real queries.
* **Groq's role.** It reads the search text and returns JSON. It does not write SQL, rank candidates or touch the database.
* **Security.** All values go through `%s` parameters; only fixed SQL text is built with f-strings.
  Table and column names are never taken from user input.

## Setup

```bash
docker compose up -d db                        # postgres with pgvector (image pgvector/pgvector:pg16)
psql "$DATABASE_URL" -f sql/schema.sql         # fresh database
psql "$DATABASE_URL" -f sql/migrations/001_pgvector_candidate_search.sql   # existing database
# .env: USE_DATABASE=true, DATABASE_URL=..., optional GROQ_API_KEY
python -m src.database.load_candidates         # sample parsed resumes
python -m scripts.ingest_synthetic             # (optional) bulk data, then:
python -m scripts.backfill_embeddings
streamlit run app.py
```

## Tests

`tests/test_query_understanding.py` needs nothing. `tests/test_db_search.py` needs PostgreSQL with pgvector:

```bash
TEST_DATABASE_ADMIN_URL=postgresql://postgres:postgres@localhost:5432/postgres pytest tests/test_db_search.py
```

It creates and drops its own database and replaces the embedding model with a small deterministic
stand-in, so no model download is needed (its similarity numbers are not real MiniLM values).

## Known limits

* Search quality depends on the parser and on the embedding model; the similarity cut-off is tuned by hand.
* Only a short profile (skills, education, experience) is embedded, not the whole resume.
* Resumes that are scanned images are not read (no OCR).
* A single connection per unit of work (`db_session`); add a pool (`psycopg2.pool`) or PgBouncer for many concurrent users.
* No bias audit of the embedding model; keep a human in the decision.
