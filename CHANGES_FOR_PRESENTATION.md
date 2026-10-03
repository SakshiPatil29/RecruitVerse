# Changes made to address the "purely keyword matching" feedback

## 1. Fixed: Candidate Search was keyword-only for your uploaded batch
**File:** `src/retrieval/search_candidates.py`

The search over your live-uploaded resumes used literal substring matching
(`if word in skills_text`). This is why "data visualization" found nothing
while "power bi" did — there was no shared text, and this function never
looked at embeddings at all.

It now ranks the uploaded batch by Sentence-Transformer cosine similarity
between the query and each candidate's resume text (`_semantic_rank_session`),
with an exact keyword match still guaranteed to surface (so nothing that
worked before regresses), and automatically falls back to the old
keyword-only behavior if the embedding model isn't available on the
machine running it.

## 2. Added: FAISS vector index for the knowledge base
**New file:** `src/knowledge_base/vector_index.py`
**Changed:** `src/knowledge_base/dataset_loader.py`, `requirements.txt`

Knowledge-base search (the large external dataset corpus) previously
computed cosine similarity against every record in a plain Python loop.
It now uses a FAISS `IndexFlatIP` (inner product over L2-normalized
vectors = cosine similarity), cached per-process and rebuilt automatically
when the index file changes. Falls back to an equivalent brute-force numpy
scan if `faiss-cpu` isn't installed — verified to produce identical scores
in `tests/test_vector_index.py`.

## 3. Expanded the API to cover every sidebar module
**File:** `src/api/routes.py`

Added `/resume/parse`, `/ai/strengths-weaknesses`, `/ai/explanation`,
`/ai/resume-improvements` — there's now a route behind every page (JD,
Resume Upload, Screening/Ranking, Candidate Details, Search, AI Insights).

**Be accurate about this in the presentation:** the Streamlit UI calls
these Python functions directly, in-process — it does not call its own
API over HTTP. The API is a separate, legitimate integration surface (for
another service or a batch job to use), not a proof that the UI itself
is "API-driven." Say that plainly if asked.

## 4. Settings page now shows which backend is actually running
**File:** `src/ui/pages/settings.py`

Displays whether similarity scoring is using real embeddings or the
lexical fallback, and whether the knowledge base is using FAISS or the
brute-force fallback — so a degraded backend is never silently presented
as the full one, and you can screenshot this during a viva to prove which
path is live.

## 5. Evaluation scripts (new: `scripts/eval/`)
Run these to generate the numbers/tables for your slides:

```bash
python -m scripts.eval.evaluate_search           # Precision/Recall: old keyword vs new semantic search
python -m scripts.eval.evaluate_ranking          # Ablation: skill-only vs semantic-only vs blended
python -m scripts.eval.compare_embedding_backend # Real embeddings vs lexical fallback, same inputs
```

`scripts/eval/sample_candidates.py` is a small (16-person) hand-built,
hand-labeled candidate set — the bundled repo doesn't include the large
external datasets, so this lets anyone reproduce the evaluation without
downloading them first.

### Important honesty note
This sandbox couldn't install `sentence-transformers`/`torch` (disk-space
limited), so everything above was tested and verified against the
project's own **lexical fallback** path, not the real transformer model.
Code correctness, math, and control flow are verified (18/18 tests pass,
including 9 new tests). The specific "data visualization -> Power BI"
semantic association will only show up once you run these scripts on a
machine with `pip install -r requirements.txt` fully installed (the real
model is what supplies word-meaning, not just word-overlap). Run
`evaluate_search.py` locally before your presentation and use that output
— it'll show a real precision/recall gap the lexical fallback can't
reproduce.

## 7. Fixed: wrong name extracted from resumes with a top-of-page table
**File:** `src/parser/resume_parser.py`

`extract_name()` used to scan the first 10 lines of the *flattened* text
and grab the first 2-4-word, mostly-alphabetic line — no notion of table
structure. When a resume opens with a "Personal Details" style table, the
flattened text can put a table's own header/label row (e.g. "Name Email
Phone Address") ahead of the actual name, and that label row passes the
exact same alphabetic/word-count test a real name would pass — so it gets
returned instead.

Fix, in priority order (same pattern already used for experience/date
tables via `extract_tables()`):
1. **New: table-aware lookup first** (`_name_from_tables`) — looks for a
   cell literally labeled "Name" / "Full Name" / "Candidate Name" /
   "Employee Name" / "Applicant Name" in the structured table data (which
   preserves real row/column structure, unlike flattened text), and reads
   the adjacent or below cell as the value. Handles both label-value-pair
   rows and header-row-then-data-row layouts.
2. **Hardened fallback** — the original line-scanning heuristic now also
   rejects a line if every word in it is a known field-label word (name,
   email, phone, address, dob, etc.), so a flattened label row can't be
   mistaken for a name even without table data.
3. Falls through to `"Unknown"` exactly as before if neither path finds
   anything — no behavior change for resumes this already worked on.

Verified against all 4 bundled real resumes (still parse correctly) and
a real PDF with an actual PyMuPDF-detected table (correct name extracted
via the table path). 7 new tests in `tests/test_name_extraction.py`.

**Caveat:** the exact way a table's text flattens depends on the specific
PDF's fonts/layout, so I couldn't perfectly reproduce your exact failure
with a synthetic file — if you still have the resume that showed the
wrong name, send it over and I'll verify against that exact file.

## Candidate Search: PostgreSQL + pgvector (database path)
**New files:** `src/retrieval/db_search.py`, `src/retrieval/query_understanding.py`,
`src/retrieval/profile_text.py`, `sql/migrations/001_pgvector_candidate_search.sql`,
`scripts/backfill_embeddings.py`, `docs/CANDIDATE_SEARCH.md`,
`tests/test_db_search.py`, `tests/test_query_understanding.py`, `.gitignore`
**Changed:** `src/database/load_candidates.py`, `src/config/db.py`,
`src/config/settings.py`, `src/retrieval/search_candidates.py`,
`src/ui/pages/candidate_search.py`, `src/ui/pages/resume_upload.py`,
`src/ui/pages/settings.py`, `src/ai/groq_client.py` (two optional arguments),
`sql/schema.sql`, `docker-compose.yml` (pgvector image), `requirements.txt`, `.env.example`

Candidates saved in PostgreSQL can now be found by meaning, not just by exact
skill. Each candidate gets a short profile text (skills, education,
experience) that is embedded with the same all-MiniLM-L6-v2 model and stored in
a `vector(384)` column with an HNSW index. A search runs as one SQL statement:
exact rules (years, must-have skills) in `WHERE`, meaning in
`ORDER BY embedding <=> query_vector`. The FAISS knowledge-base search and the
uploaded-batch search are unchanged and still work with no database.

* The recruiter's text is turned into filters by Groq (JSON only, validated) with a
  regex fallback. Groq never writes SQL and never ranks candidates.
* Loading is idempotent (same e-mail updates the row); each file is isolated by a
  savepoint so one bad resume does not lose the batch.
* `scripts/backfill_embeddings.py` embeds rows added by the bulk `ingest_*` scripts.
* Resumes parsed in the UI are saved to PostgreSQL when `USE_DATABASE=true`.
* Behaviour to know: a "3+ years" rule excludes candidates whose experience is
  unknown (NULL); if no stored candidate has every must-have skill the search falls
  back to meaning-only and says so on the page.

