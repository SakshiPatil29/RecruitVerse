"""Tests for src/knowledge_base/vector_index.py — checks the FAISS path
and the brute-force fallback return the same top result and score for the
same input, so the fallback is a true drop-in, not just "close enough"."""

import numpy as np
import pytest

from src.knowledge_base.vector_index import VectorIndex


def _make_vectors(n=20, dim=8, seed=0):
    rng = np.random.default_rng(seed)
    vectors = rng.standard_normal((n, dim)).astype("float32")
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    records = [{"name": f"cand_{i}"} for i in range(n)]
    return vectors, records


def test_exact_match_scores_close_to_one():
    vectors, records = _make_vectors()
    index = VectorIndex(vectors, records)

    results = index.search(vectors[5], top_k=3)

    assert results[0][1]["name"] == "cand_5"
    assert results[0][0] == pytest.approx(1.0, abs=1e-4)


def test_results_sorted_descending():
    vectors, records = _make_vectors()
    index = VectorIndex(vectors, records)

    results = index.search(vectors[0], top_k=5)
    scores = [score for score, _ in results]

    assert scores == sorted(scores, reverse=True)


def test_top_k_respected():
    vectors, records = _make_vectors(n=20)
    index = VectorIndex(vectors, records)

    results = index.search(vectors[0], top_k=4)

    assert len(results) == 4


def test_brute_force_fallback_matches_faiss_path(monkeypatch):
    import src.knowledge_base.vector_index as vi

    vectors, records = _make_vectors()

    faiss_index = VectorIndex(vectors, records)
    faiss_results = faiss_index.search(vectors[3], top_k=3)

    monkeypatch.setattr(vi, "_FAISS_AVAILABLE", False)
    monkeypatch.setattr(vi, "faiss", None)
    brute_force_index = vi.VectorIndex(vectors, records)
    brute_force_results = brute_force_index.search(vectors[3], top_k=3)

    assert [name for _, r in faiss_results for name in [r["name"]]] == \
           [name for _, r in brute_force_results for name in [r["name"]]]
    for (faiss_score, _), (bf_score, _) in zip(faiss_results, brute_force_results):
        assert faiss_score == pytest.approx(bf_score, abs=1e-4)


def test_empty_index_returns_empty_list():
    index = VectorIndex(np.zeros((0, 8), dtype="float32"), [])
    assert index.search(np.zeros(8, dtype="float32"), top_k=5) == []
