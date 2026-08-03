"""
ATS API routes.

A thin HTTP surface over the same modules the Streamlit UI uses, so the
screening pipeline is reachable programmatically (e.g. from another
service or a batch job). The old routes wired into workflow/governance/
mlops/notification modules that no longer exist; these expose only the
resume-screening workflow.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.ai import insights
from src.parser.jd_parser import parse_jd_text
from src.parser.resume_parser import parse_resume_text
from src.pipeline.screening_pipeline import screen_candidates
from src.retrieval.search_candidates import semantic_search

router = APIRouter()


# ---------- models ----------

class JDRequest(BaseModel):
    text: str
    job_title: str | None = None


class ScreenRequest(BaseModel):
    jd_text: str
    resumes: list[str]  # raw resume texts


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10


class InsightRequest(BaseModel):
    candidate: dict
    jd: dict | None = None


# ---------- job description ----------

@router.post("/jd/parse")
def parse_job_description(payload: JDRequest):
    parsed = parse_jd_text(payload.text)
    parsed["job_title"] = payload.job_title or "Untitled role"
    return parsed


# ---------- screening ----------

@router.post("/screen")
def screen(payload: ScreenRequest):
    """Parse a JD + a list of raw resume texts, then rank the candidates."""
    if not payload.resumes:
        raise HTTPException(status_code=400, detail="No resumes provided.")

    jd = parse_jd_text(payload.jd_text)
    resumes = [parse_resume_text(text) for text in payload.resumes]
    ranked = screen_candidates(jd, resumes)

    # Strip raw_text from the response to keep it lightweight.
    for candidate in ranked:
        candidate.pop("raw_text", None)
    return {"job": {"required_skills": jd["required_skills"]}, "candidates": ranked}


# ---------- search ----------

@router.post("/search")
def search(payload: SearchRequest):
    return semantic_search(payload.query, top_k=payload.top_k)


# ---------- AI insights ----------

@router.post("/ai/summary")
def ai_summary(payload: InsightRequest):
    return {"summary": insights.generate_summary(payload.candidate)}


@router.post("/ai/recommendation")
def ai_recommendation(payload: InsightRequest):
    return {"recommendation": insights.generate_hiring_recommendation(payload.candidate)}


@router.post("/ai/questions")
def ai_questions(payload: InsightRequest):
    return {"questions": insights.generate_interview_questions(payload.candidate, payload.jd or {})}


@router.post("/ai/jd-summary")
def ai_jd_summary(payload: InsightRequest):
    return {"summary": insights.generate_jd_summary(payload.jd or payload.candidate)}
