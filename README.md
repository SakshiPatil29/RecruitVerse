# RecruitVerse — AI-Powered Resume Screening & Candidate Ranking System (ATS)

> An intelligent Applicant Tracking System that reads a job description and a batch of resumes, then ranks candidates by **semantic similarity + skill match** — with a clear, explainable reason behind every score.

Built as the final project for **PGCP Big Data Analytics, CDAC Innovation Park, Pune.**

---

## 📌 Overview

Recruiters often receive hundreds of resumes for a single role. Reading them by hand is slow, inconsistent, and hard to justify. **RecruitVerse** automates this: a recruiter uploads one job description and a batch of resumes, and in seconds gets a **ranked, explained shortlist** of candidates.

The core scoring is **deterministic and reproducible** — the same inputs always produce the same score — and every score comes with a transparent breakdown of matched, missing, and additional skills. An optional local LLM adds AI-generated summaries, hiring recommendations, and interview questions, but **never affects the score**.

---

## ✨ Key Features

- **Multi-format parsing** — reads resumes and job descriptions from **PDF, DOCX, and TXT**.
- **Semantic matching** — uses Sentence-Transformers embeddings and cosine similarity to compare *meaning*, not just keywords.
- **Explainable weighted scoring** — `Skill Match (50%) + Semantic Similarity (30%) + Experience (20%)`.
- **Skill gap analysis** — matched / missing / additional skills for every candidate.
- **Candidate ranking** — sortable shortlist with score breakdowns and visual analytics.
- **Semantic candidate search** — natural-language search over a resume knowledge base.
- **AI insights (optional)** — resume summaries, hiring recommendations, and interview questions via a local LLM, with rule-based fallbacks so the app works offline.
- **Graceful degradation** — runs fully without a database, and without the LLM or embedding model (falls back to a lexical similarity method).

---

## 🧠 How the Match Score Works

The final score is a **deterministic weighted blend** of three components (each scored 0–100):

| Component | Weight | How it's computed |
|-----------|:------:|-------------------|
| **Skill Match** | 50% | Fraction of the JD's required skills present in the resume |
| **Semantic Similarity** | 30% | Cosine similarity between the resume and JD embeddings |
| **Experience** | 20% | Candidate's years vs the years the JD requires |

```
Final Score = (0.50 × Skill Match) + (0.30 × Semantic Similarity) + (0.20 × Experience)
```

> **The AI never decides the score.** Scoring uses only embeddings, cosine similarity, and skill counting — so it's reproducible and defensible. The LLM (Ollama) is used *only* for narrative text (summaries, questions, recommendations).

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python |
| **Web UI** | Streamlit |
| **REST API** | FastAPI + Uvicorn |
| **Semantic Matching** | Sentence-Transformers (`all-MiniLM-L6-v2`), PyTorch |
| **NLP / Parsing** | PyMuPDF (PDF), python-docx (DOCX), regular expressions |
| **Data** | pandas, NumPy |
| **AI Narrative (optional)** | Ollama (local LLM) |
| **Persistence (optional)** | PostgreSQL, SQLAlchemy, psycopg2 |
| **Testing** | pytest |

---

## 🏗️ Architecture

RecruitVerse follows a clean, layered architecture — the UI is separated from the deterministic logic, which is separated from the AI and data layers.

```
Job Description  →  Resume Upload  →  Parsing  →  Semantic Matching
                 →  Skill Extraction  →  Ranking  →  Explanation & AI Insights
```

```
app.py                     # Streamlit entry point (routing only)
src/
  parser/                  # file_extractor, resume_parser, jd_parser
  matching/                # embedding_matcher (semantic), skill_matcher, skill_extractor
  ranking/                 # scoring_engine, candidate_ranker, analytics
  explainability/          # deterministic ✓/✗ score explanations
  ai/                      # ollama_client + insights (with rule-based fallbacks)
  pipeline/                # screening_pipeline (parse → match → score → rank)
  knowledge_base/          # dataset loaders + vector search index
  retrieval/               # candidate search
  ui/                      # theme, state, and the 8 pages
  api/                     # FastAPI routes over the same pipeline
data/                      # skills dictionary + datasets
sql/schema.sql             # optional PostgreSQL schema
tests/                     # automated tests
```

The app has **8 pages**: Dashboard, Job Description, Resume Upload, Candidate Ranking, Candidate Details, Candidate Search, AI Insights, and Settings.

---

## 🔮 Future Scope

- Bias & fairness auditing for equitable screening
- Vector database (FAISS / pgvector) to scale search to millions of resumes
- ATS / job-board integrations (LinkedIn, Naukri, Greenhouse)
- Fine-tuned domain-specific embedding models
- OCR support for scanned-image resumes
- Authentication & multi-tenant SaaS deployment

---

## 👥 Team

Developed by a team of 5 as the final project for **PGCP Big Data Analytics, CDAC Innovation Park, Pune.**

- Sakshi Patil
- Rupali Kale
- Atishee Jain
- Vijaya Nanaware
- Ridhi Jain

---

## 📄 License

This project was created for academic purposes as part of the CDAC PGCP-BDA program.
