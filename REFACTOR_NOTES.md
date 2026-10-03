# Refactor notes — RecruitVerse → RecruitVerse ATS

What changed when the original RecruitVerse (a broad HR suite) was refactored
into a focused Resume Screening & Ranking ATS.

## Removed (out of scope)
Modules: `workflow/`, `governance/`, `monitoring/`, `mlops/`, `notifications/`,
`events/`, `talent_intelligence/`, `recommendation_engine/`, `optimization/`,
`pipeline/scheduler.py`, `services/` (shortlist/notification/interview/etc.).
UI: all 14 dashboards (executive, BI, workflow, talent, recommendations,
comparison, governance, mlops, data lake, events, notifications, performance…).
SQL/tests/infra tied to the above. Also dropped: `analytics/`, `presentation/`,
`deployment/`, `release/`, `reports/`, `screenshots/`, `notebooks/`, `demo/`,
`etl/`, `warehouse/`, `data_lake/`, `shap` dependency.

## Reused from the original
- `matching/skill_extractor.py` + `data/skills_dictionary/` (unchanged)
- `parser/` regex primitives (email/phone/name/education/experience)
- `config/db.py`, `database/load_*.py`
- `scripts/ingest_*.py`, `refresh_skill_usage.py`, `backup_database.py`
- `explainability/feature_importance.py` weights → now `config/settings.RANKING_WEIGHTS`
- `interview_assistant/question_generator.py` (as the AI-fallback path)
- `search/candidate_filters.py`, `candidate_search.py`

## New / rebuilt
- `parser/file_extractor.py` — one PDF/DOCX/TXT extractor (replaced PDF-only script)
- `parser/resume_parser.py` — now extracts certs, projects, companies, summary; any format
- `parser/jd_parser.py` — required vs preferred skills
- `matching/embedding_matcher.py` — **real** Sentence-Transformers semantic similarity
  (the original `semantic_matcher.py` was set-overlap; kept only for `normalize_skill`)
- `matching/skill_matcher.py` — matched / missing / **additional** skills
- `ranking/scoring_engine.py` — weighted final score (50/30/20)
- `ranking/candidate_ranker.py` — rank + medals; `ranking/analytics.py` — cohort charts
- `explainability/score_explainer.py` — structured ✓/✗ reasons (LLM-independent)
- `ai/groq_client.py` + `ai/insights.py` — all AI narrative, each with a fallback
- `pipeline/screening_pipeline.py` — the deterministic parse→match→score→rank path
- `knowledge_base/dataset_loader.py` — vector index over the 3 datasets for search
- `retrieval/search_candidates.py` — unified batch + knowledge-base search
- `ui/` — theme, state, and 8 pages; `app.py` — router only
- `api/routes.py` — trimmed to the ATS pipeline

## Key design rules
- **Scoring is deterministic.** Groq never computes similarity or rank.
- **Works with no DB and no Groq key.** Both are optional; fallbacks everywhere.
- **Datasets are backend-only.** Recruiters never browse them; they power search.

## Not yet done (do in Claude Code with real deps)
- End-to-end run against a live embedding model + Streamlit UI
- First-run model download, Groq live test, Postgres persistence path
- `pytest tests/test_pipeline.py` (verified manually here; pytest wasn't installable in the sandbox)
