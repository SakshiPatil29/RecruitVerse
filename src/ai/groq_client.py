"""
Groq client.

Groq is used exclusively for recruiter-facing narrative text: resume
summaries, strengths/weaknesses, hiring recommendations, explanations,
interview questions, resume improvement tips, and JD summaries. It is
never used to compute a similarity score or a ranking — those stay
deterministic (src/matching/embedding_matcher.py,
src/matching/skill_matcher.py, src/ranking/scoring_engine.py).

One more narrow use: src/retrieval/query_understanding.py asks Groq to turn
the recruiter's search text into a small JSON of filters. The reply is
validated before use, Groq never writes SQL, and it never touches the
database.

Every function here degrades gracefully: if GROQ_API_KEY isn't set or a
request fails, callers get None back and fall back to the rule-based
equivalents in src/ai/insights.py so the app still works without an LLM.
"""

from groq import Groq

from src.config.settings import GROQ_API_KEY, GROQ_MODEL, GROQ_TIMEOUT_SECONDS

_client = None


def _get_client():
    global _client
    if not GROQ_API_KEY:
        return None
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY, timeout=GROQ_TIMEOUT_SECONDS)
    return _client


def is_available():
    """Whether a Groq API key is configured. This is a cheap local check,
    not a live network call — a configured key can still fail at request
    time (bad key, quota, outage), which generate() handles below."""
    return _get_client() is not None


def generate(prompt, system=None, model=None, temperature=None, json_mode=False):
    """Call Groq's chat completions endpoint. Returns the generated text,
    or None if no API key is configured or the request fails.

    temperature: pass 0 for repeatable answers (used for query parsing).
    json_mode:   ask the model to reply with a JSON object only."""

    client = _get_client()
    if client is None:
        return None

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    options = {}
    if temperature is not None:
        options["temperature"] = temperature
    if json_mode:
        options["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(
            model=model or GROQ_MODEL,
            messages=messages,
            **options,
        )
        return (response.choices[0].message.content or "").strip() or None
    except Exception:
        return None
