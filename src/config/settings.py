"""
Central configuration for RecruitVerse ATS.

Everything that used to be scattered magic numbers/strings across the old
dashboards lives here now, so the app can be tuned (models, weights,
Ollama host, dataset locations) from one place or via environment
variables — no code changes needed to point at a different embedding
model or a remote Ollama instance.
"""

import os

# ---------------------------------------------------------------------------
# Database (optional). The app works fully in-memory (session-only) with no
# database configured — persistence is a bonus, not a requirement, so the
# recruiter workflow described in the spec works out of the box.
# ---------------------------------------------------------------------------
USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Semantic matching
# ---------------------------------------------------------------------------
# Any sentence-transformers model works; all-MiniLM-L6-v2 is small/fast and
# a good default for CPU-only recruiter laptops. Swap via env var if a GPU
# box wants the higher-quality mpnet or bge models instead.
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

# ---------------------------------------------------------------------------
# Ranking weights — reused from the old
# src/explainability/feature_importance.FEATURE_WEIGHTS, now the single
# source of truth for how a candidate's final score is composed.
# ---------------------------------------------------------------------------
RANKING_WEIGHTS = {
    "skill_match": 0.5,
    "semantic_similarity": 0.3,
    "experience": 0.2,
}

# ---------------------------------------------------------------------------
# Ollama — used ONLY for narrative/explanatory AI features (summaries,
# strengths/weaknesses, hiring recommendation, interview questions, resume
# improvement tips, JD summaries). It never computes similarity or ranking.
# ---------------------------------------------------------------------------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "30"))

# ---------------------------------------------------------------------------
# Dataset-backed knowledge base. These datasets are backend-only resources
# for semantic search / retrieval — recruiters never browse them directly.
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "data", "knowledge_base")
KNOWLEDGE_BASE_INDEX_PATH = os.path.join(KNOWLEDGE_BASE_DIR, "kb_index.pkl")

DATASET_SOURCES = {
    # "Relational 54K" — structured people/skills/education/experience CSVs.
    "relational_54k": os.path.join(BASE_DIR, "data", "imports", "relational_54k"),
    # LiveCareer-style real resumes (PDF + structured CSV export).
    "real": os.path.join(BASE_DIR, "data", "raw_resumes", "real"),
    # Synthetic resume corpus.
    "synthetic": os.path.join(BASE_DIR, "data", "raw_resumes", "synthetic"),
}

# Cap how many rows/files we embed per source when building the knowledge
# base index — these datasets are large (tens of thousands of resumes) and
# a recruiter-facing semantic search doesn't need all of them indexed to be
# useful. Raise this from an env var for a full offline rebuild.
KNOWLEDGE_BASE_SAMPLE_SIZE = int(os.getenv("KNOWLEDGE_BASE_SAMPLE_SIZE", "3000"))
