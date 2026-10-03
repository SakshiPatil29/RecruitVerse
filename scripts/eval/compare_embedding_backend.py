"""
Forces the deterministic lexical fallback and compares it against real
Sentence-Transformer embeddings (when available) on the same JD/candidate
batch, to show the embedding step is doing real semantic work rather than
returning a fixed/arbitrary number.

Usage:
    python -m scripts.eval.compare_embedding_backend

Requires sentence-transformers installed to show the "real embeddings"
column; otherwise it reports the lexical-only scores and says so plainly
rather than faking a comparison.
"""

from src.matching import embedding_matcher
from scripts.eval.sample_candidates import CANDIDATES

JD_TEXT = (
    "We are hiring an analyst with strong data visualization experience to build "
    "dashboards and reports for leadership. Must be comfortable with SQL and Excel; "
    "Python is a plus."
)


def _lexical_scores():
    # semantic_similarity_score() picks embeddings if available; to force
    # the lexical path specifically we call the private lexical function
    # directly, mirroring how embedding_matcher falls back internally.
    from src.matching.embedding_matcher import _lexical_similarity  # noqa: SLF001
    return [round(_lexical_similarity(JD_TEXT, c["raw_text"]) * 100, 2) for c in CANDIDATES]


def main():
    backend = embedding_matcher.semantic_backend()
    print(f"Detected backend on this machine: {backend}\n")

    lexical = _lexical_scores()

    if backend == "embeddings":
        real = list(embedding_matcher.rank_by_semantic_similarity(
            [c["raw_text"] for c in CANDIDATES], JD_TEXT
        ))
        print(f"{'Candidate':<16}{'Lexical fallback':>18}{'Real embeddings':>18}{'Delta':>10}")
        for c, lex, emb in zip(CANDIDATES, lexical, real):
            print(f"{c['name']:<16}{lex:>18.2f}{emb:>18.2f}{emb - lex:>10.2f}")
        print(
            "\nBoth columns score the same JD/resume pairs. Differences show the "
            "transformer model picking up on paraphrase/synonym relationships "
            "(e.g. 'data visualization' vs 'Power BI') that word-overlap scoring can't."
        )
    else:
        print(
            "sentence-transformers isn't installed in this environment, so only the "
            "lexical fallback is available to compare against. Install it "
            "(`pip install sentence-transformers`, ~90MB model download) and re-run "
            "this script to see the real-embeddings column.\n"
        )
        print(f"{'Candidate':<16}{'Lexical fallback':>18}")
        for c, lex in zip(CANDIDATES, lexical):
            print(f"{c['name']:<16}{lex:>18.2f}")


if __name__ == "__main__":
    main()
