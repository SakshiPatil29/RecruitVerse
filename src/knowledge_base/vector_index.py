"""
FAISS-backed vector index for the knowledge-base semantic search.

Before this module, semantic_search() in dataset_loader.py computed
cosine similarity against every record in a plain Python loop — correct,
but not actually "vector search infrastructure," just a linear scan. This
wraps the same normalized Sentence-Transformer embeddings
(embedding_matcher.embed_texts uses normalize_embeddings=True) in a FAISS
IndexFlatIP, so inner product == cosine similarity and lookups use a real
vector index.

Falls back to an equivalent brute-force numpy scan (identical math, just
without FAISS) if the optional faiss-cpu package isn't installed, so nothing
breaks on a machine that skipped that dependency — same fallback pattern
embedding_matcher.py already uses for the embedding model itself.
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)

try:
    import faiss
    _FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    _FAISS_AVAILABLE = False
    logger.warning(
        "faiss is not installed; falling back to a brute-force cosine scan "
        "for knowledge-base search. Run: pip install faiss-cpu"
    )


def faiss_available():
    """True when real FAISS indexing is in use (vs. the brute-force
    fallback). Surfaced on the Settings page so a degraded backend is
    never presented as the accelerated one."""
    return _FAISS_AVAILABLE


def vector_backend():
    return "faiss" if _FAISS_AVAILABLE else "brute_force_numpy"


class VectorIndex:
    """A queryable similarity index over a fixed list of (embedding, record)
    pairs. Records can be any dict payload — the index itself only cares
    about the vectors."""

    def __init__(self, embeddings, records):
        if len(embeddings) != len(records):
            raise ValueError("embeddings and records must be the same length")

        self.records = records
        vectors = np.asarray(embeddings, dtype="float32")

        if vectors.size == 0 or len(records) == 0:
            self._dim = 0
            self._vectors = vectors
            self._index = None
            return

        self._dim = vectors.shape[1]
        self._vectors = vectors
        self._index = None

        if _FAISS_AVAILABLE:
            index = faiss.IndexFlatIP(self._dim)
            index.add(vectors)
            self._index = index

    def __len__(self):
        return len(self.records)

    def search(self, query_vector, top_k=10):
        """Return [(similarity, record), ...] sorted by similarity desc,
        highest first. similarity is a cosine similarity in [-1, 1]
        (typically 0.2-0.9 for related-to-identical text, same band as
        embedding_matcher.cosine_similarity)."""

        if self._dim == 0:
            return []

        query = np.asarray(query_vector, dtype="float32").reshape(1, -1)
        top_k = max(1, min(top_k, len(self.records)))

        if self._index is not None:
            scores, indices = self._index.search(query, top_k)
            return [
                (float(score), self.records[idx])
                for score, idx in zip(scores[0], indices[0])
                if idx != -1
            ]

        # Brute-force fallback. Vectors are already L2-normalized (see
        # embed_texts), so a plain dot product equals cosine similarity —
        # identical math to the FAISS path, just O(n) per query.
        similarities = self._vectors @ query[0]
        top_indices = np.argsort(-similarities)[:top_k]
        return [(float(similarities[i]), self.records[i]) for i in top_indices]
