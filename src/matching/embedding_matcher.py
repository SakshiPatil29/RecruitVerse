"""
Embedding-based semantic matching.

This is new: the original codebase had no real semantic similarity — its
"semantic_matcher.py" was actually just a skill-set overlap calculation
(see skill_matcher.py, which keeps that logic under an honest name). This
module adds genuine Sentence-Transformers embeddings and is the ONLY
place cosine similarity is computed, so ranking stays deterministic and
reproducible. Ollama is never used for scoring — see src/ai/insights.py
for where the LLM is (and isn't) involved.

Sentence-Transformers is a heavy optional dependency (it pulls in torch)
and the model is downloaded on first use, so either step can be missing on
a fresh machine. Rather than let that abort the whole Streamlit script —
which renders as a blank page, not an error the recruiter can act on — we
fall back to a deterministic lexical cosine over word frequencies. Scores
are less nuanced but the workflow keeps working; call semantic_backend()
to find out which path is live and tell the user.
"""

import logging
import math
import re
from collections import Counter
from functools import lru_cache

from src.config.settings import EMBEDDING_MODEL_NAME

logger = logging.getLogger(__name__)

# Cosine similarity for sentence embeddings sits in a compressed band
# (roughly 0.2-0.9 for related-to-identical text) rather than spanning the
# full 0-1 range, so a raw *100 reads deceptively low to a recruiter.
# Rescale against a practical floor.
_SIMILARITY_FLOOR = 0.2
_SIMILARITY_SPAN = 0.7

_TOKEN_RE = re.compile(r"[a-z0-9+#.]+")


@lru_cache(maxsize=1)
def _get_model():
    """Load the Sentence-Transformers model once per process. Cached so
    Streamlit reruns (and repeated calls within a batch) don't reload the
    model from disk every time.

    Returns None when the library isn't installed or the model can't be
    loaded (no network on first run, corrupt cache); callers then use the
    lexical fallback."""

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.warning(
            "sentence-transformers is not installed; falling back to lexical "
            "similarity for semantic scores. Run: pip install sentence-transformers"
        )
        return None
    except Exception as exc:
        # Not just ImportError: a torch whose native libraries fail to load
        # raises OSError from this import (see src/config/runtime.py).
        logger.warning(
            "sentence-transformers could not be imported (%s); falling back to "
            "lexical similarity for semantic scores.", exc
        )
        return None

    try:
        return SentenceTransformer(EMBEDDING_MODEL_NAME)
    except Exception as exc:  # model download / cache failure
        logger.warning(
            "Could not load embedding model %r (%s); falling back to lexical "
            "similarity for semantic scores.", EMBEDDING_MODEL_NAME, exc
        )
        return None


def embeddings_available():
    """True when real Sentence-Transformers embeddings are in use."""
    return _get_model() is not None


def semantic_backend():
    """Which similarity path is live: 'embeddings' or 'lexical'. The UI
    surfaces this so a degraded score is never presented as a full one."""
    return "embeddings" if embeddings_available() else "lexical"


def embed_texts(texts):
    """Encode a list of strings into embedding vectors (numpy array).

    Raises RuntimeError if the model is unavailable — use
    rank_by_semantic_similarity/semantic_similarity_score instead if you
    want the automatic fallback."""

    model = _get_model()
    if model is None:
        raise RuntimeError(
            "Embedding model unavailable — install sentence-transformers "
            "or use rank_by_semantic_similarity(), which falls back."
        )
    return model.encode(list(texts), convert_to_numpy=True, normalize_embeddings=True)


def embed_text(text):
    return embed_texts([text])[0]


def cosine_similarity(vec_a, vec_b):
    import numpy as np

    denom = (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
    if denom == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / denom)


def _rescale(similarity):
    """Map a raw cosine similarity onto the 0-100 score recruiters see."""
    similarity = max(0.0, min(1.0, (similarity - _SIMILARITY_FLOOR) / _SIMILARITY_SPAN))
    return round(similarity * 100, 2)


def _tokenize(text):
    return _TOKEN_RE.findall((text or "").lower())


def _lexical_similarity(text_a, text_b):
    """Cosine similarity over word-frequency vectors — no dependencies, no
    model download, fully deterministic. Used when embeddings are absent."""

    counts_a = Counter(_tokenize(text_a))
    counts_b = Counter(_tokenize(text_b))
    if not counts_a or not counts_b:
        return 0.0

    shared = set(counts_a) & set(counts_b)
    dot = sum(counts_a[token] * counts_b[token] for token in shared)
    norm_a = math.sqrt(sum(count * count for count in counts_a.values()))
    norm_b = math.sqrt(sum(count * count for count in counts_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def semantic_similarity_score(resume_text, jd_text):
    """Full-resume vs full-JD semantic similarity, as a 0-100 score."""
    if _get_model() is None:
        return _rescale(_lexical_similarity(resume_text, jd_text))

    resume_vec, jd_vec = embed_texts([resume_text, jd_text])
    return _rescale(cosine_similarity(resume_vec, jd_vec))


def rank_by_semantic_similarity(resume_texts, jd_text):
    """Batch version: embed the JD once and every resume once, return
    scores in the same order as resume_texts. Used by candidate ranking
    so a batch of 4-20 resumes only costs one JD embedding + one batched
    resume embedding call, not N separate calls."""

    resume_texts = list(resume_texts)
    if not resume_texts:
        return []

    if _get_model() is None:
        return [_rescale(_lexical_similarity(text, jd_text)) for text in resume_texts]

    all_vecs = embed_texts(resume_texts + [jd_text])
    jd_vec = all_vecs[-1]
    return [_rescale(cosine_similarity(vec, jd_vec)) for vec in all_vecs[:-1]]
