"""
Ollama client.

Ollama is used exclusively for recruiter-facing narrative text: resume
summaries, strengths/weaknesses, hiring recommendations, explanations,
interview questions, resume improvement tips, and JD summaries. It is
never used to compute a similarity score or a ranking — those stay
deterministic (src/matching/embedding_matcher.py,
src/matching/skill_matcher.py, src/ranking/scoring_engine.py).

Every function here degrades gracefully: if Ollama isn't running or the
request fails, callers get None back and fall back to the rule-based
equivalents in src/ai/insights.py so the app still works without an LLM.
"""

import json

import requests

from src.config.settings import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS


def is_available():
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        return response.status_code == 200
    except requests.RequestException:
        return False


def generate(prompt, system=None, model=None):
    """Call Ollama's /api/generate with a single prompt. Returns the
    generated text, or None if Ollama is unreachable or errors out."""

    payload = {
        "model": model or OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip() or None
    except (requests.RequestException, json.JSONDecodeError):
        return None
