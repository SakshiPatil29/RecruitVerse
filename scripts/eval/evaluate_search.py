"""
Evaluates Candidate Search: old keyword-only matching vs. the current
embedding-based semantic search, on a small hand-labeled query set.

This is the script to run before a demo/presentation — it reproduces the
"data visualization finds nothing, but power bi does" bug on paper, with
numbers, and shows the fix.

Usage:
    python -m scripts.eval.evaluate_search

Notes on running without sentence-transformers installed: the embedding
matcher automatically falls back to a deterministic lexical similarity
(see src/matching/embedding_matcher.py) if sentence-transformers/torch
aren't available, so this script still runs and still demonstrates the
search-ranking difference — just with a coarser similarity signal than
the real transformer model gives on a full install. The header printed
below tells you which backend was actually used.
"""

from src.matching.embedding_matcher import semantic_backend
from src.retrieval.search_candidates import semantic_search
from scripts.eval.sample_candidates import CANDIDATES

# query -> set of candidate names a human reviewer would call relevant.
# This is the ground truth Precision/Recall are measured against.
LABELED_QUERIES = {
    "data visualization": {
        "Rahul Verma", "Karan Mehta", "Devansh Rao", "Ishita Bansal", "Neha Joshi", "Simran Kaur",
    },
    "power bi": {
        "Rahul Verma", "Ishita Bansal", "Neha Joshi",
    },
    "backend api development": {
        "Priya Sharma", "Vikram Singh", "Rohan Desai",
    },
    "cloud infrastructure": {
        "Arjun Nair", "Ananya Iyer",
    },
    "frontend development": {
        "Sneha Kulkarni", "Farhan Ali",
    },
    "natural language processing": {
        "Aditya Kapoor",
    },
}

TOP_K = 5


def _old_keyword_search(query, candidates):
    """The exact literal-substring logic Candidate Search used before the
    fix (kept here only for comparison — it no longer exists in
    search_candidates.py)."""
    query_lower = query.lower()
    hits = []
    for candidate in candidates:
        skills_text = " ".join(candidate.get("skills", [])).lower()
        if any(word in skills_text or word in candidate["name"].lower() for word in query_lower.split()):
            hits.append(candidate["name"])
    return hits[:TOP_K]


def _new_semantic_search(query, candidates):
    results = semantic_search(query, session_candidates=candidates, top_k=TOP_K)
    return [c["name"] for c in results["uploaded_batch_matches"]]


def _precision_recall(returned, relevant):
    if not returned:
        return 0.0, 0.0
    returned_set = set(returned)
    true_positives = len(returned_set & relevant)
    precision = true_positives / len(returned_set)
    recall = true_positives / len(relevant) if relevant else 0.0
    return precision, recall


def main():
    print(f"Similarity backend in use: {semantic_backend()}")
    print(f"({'real Sentence-Transformer embeddings' if semantic_backend() == 'embeddings' else 'lexical fallback — install sentence-transformers for the real model'})")
    print("=" * 100)

    old_precisions, new_precisions = [], []
    old_recalls, new_recalls = [], []

    for query, relevant in LABELED_QUERIES.items():
        old_hits = _old_keyword_search(query, CANDIDATES)
        new_hits = _new_semantic_search(query, CANDIDATES)

        old_p, old_r = _precision_recall(old_hits, relevant)
        new_p, new_r = _precision_recall(new_hits, relevant)
        old_precisions.append(old_p)
        new_precisions.append(new_p)
        old_recalls.append(old_r)
        new_recalls.append(new_r)

        print(f"\nQuery: {query!r}   (ground truth: {sorted(relevant)})")
        print(f"  OLD keyword-only   -> {old_hits or '[]'}   "
              f"(P@{TOP_K}={old_p:.2f}, R={old_r:.2f})")
        print(f"  NEW semantic search -> {new_hits or '[]'}   "
              f"(P@{TOP_K}={new_p:.2f}, R={new_r:.2f})")

    print("\n" + "=" * 100)
    n = len(LABELED_QUERIES)
    print(f"Averages over {n} queries:")
    print(f"  OLD keyword-only    -> mean P@{TOP_K} = {sum(old_precisions)/n:.3f}   mean recall = {sum(old_recalls)/n:.3f}")
    print(f"  NEW semantic search -> mean P@{TOP_K} = {sum(new_precisions)/n:.3f}   mean recall = {sum(new_recalls)/n:.3f}")


if __name__ == "__main__":
    main()
