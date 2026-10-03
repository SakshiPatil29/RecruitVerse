"""Candidate Search — natural-language semantic search."""

import streamlit as st

from src.config.settings import USE_DATABASE
from src.retrieval.search_candidates import semantic_search
from src.ui import state
from src.ui.theme import MUTED, page_title

# Coarse ranking so free-text education values parsed off resumes (e.g.
# "B.Tech", "M.Sc") can be compared against the recruiter's minimum-level
# filter. Unrecognized/missing education ranks 0, i.e. below "Bachelor".
_EDUCATION_RANK = {
    "b.tech": 1, "b.e": 1, "b.sc": 1, "bca": 1, "bba": 1, "b.com": 1, "b.a": 1, "bachelor": 1,
    "m.tech": 2, "m.sc": 2, "mca": 2, "mba": 2, "m.com": 2, "m.a": 2, "master": 2,
    "phd": 3,
}
_EDUCATION_LEVELS = ["Any", "Bachelor", "Master", "PhD"]


def _passes_filters(candidate, min_experience, min_education):
    try:
        years = float(candidate.get("experience_years") or 0)
    except (TypeError, ValueError):
        years = 0
    if years < min_experience:
        return False

    if min_education != "Any":
        candidate_rank = _EDUCATION_RANK.get(str(candidate.get("education") or "").strip().lower(), 0)
        if candidate_rank < _EDUCATION_LEVELS.index(min_education):
            return False

    return True


def _describe_filters(filters):
    """One line telling the recruiter how their search text was understood."""
    parts = []
    if "min_years" in filters:
        parts.append(f"at least {filters['min_years']} years")
    if "max_years" in filters:
        parts.append(f"at most {filters['max_years']} years")
    if filters.get("skills"):
        parts.append("must have: " + ", ".join(filters["skills"]))
    if filters.get("semantic_text"):
        parts.append(f"meaning: {filters['semantic_text']}")
    return " | ".join(parts)


def _render_database_matches(results, min_experience, min_education):
    st.subheader("From the candidate database")
    info = results.get("database_info") or {}

    if info.get("error"):
        st.warning("The candidate database could not be searched: " + info["error"])
        return

    if info.get("filters"):
        how = "Llama" if info.get("source") == "llm" else "rules"
        st.caption(f"Understood by {how} as: {_describe_filters(info['filters'])}")
    if info.get("relaxed"):
        st.info("No stored candidate has every required skill, so these are the closest matches by meaning.")
    if info.get("mode") == "keyword":
        st.caption("Embeddings are unavailable, so this used skill keywords only.")

    matches = [c for c in results.get("database_matches", []) if _passes_filters(c, min_experience, min_education)]
    if not matches:
        st.caption("No matches in the candidate database.")
        return

    for c in matches:
        skills = ", ".join(c.get("skills", [])[:12])
        match = f" · {c['similarity']}% match" if c.get("similarity") is not None else ""
        st.markdown(f"**{c.get('name')}** · {c.get('experience_years', 'n/a')} yrs{match}")
        st.markdown(f'<span style="color:{MUTED};">{skills}</span>', unsafe_allow_html=True)
        if c.get("email"):
            st.caption(c["email"])
        st.write("")


def render():
    page_title("Candidate Search")
    st.caption("Search in natural language, e.g. \"Data Engineers with Spark\" or "
               "\"Python developers with Kafka, 3+ years\". Searches your uploaded batch, the "
               "dataset-backed knowledge base" + (" and the candidate database." if USE_DATABASE else "."))

    filter_col, edu_col = st.columns(2)
    with filter_col:
        min_experience = st.number_input(
            "Minimum years of experience", min_value=0, value=0, step=1,
        )
    with edu_col:
        min_education = st.selectbox("Minimum education level", _EDUCATION_LEVELS, index=0)

    query = st.text_input("Search", placeholder="Find ML Engineers with AWS")
    if not query:
        return

    with st.spinner("Searching..."):
        results = semantic_search(
            query, session_candidates=state.get_resumes(), top_k=10, min_experience=min_experience,
        )

    batch = [c for c in results["uploaded_batch_matches"] if _passes_filters(c, min_experience, min_education)]
    kb = [c for c in results["knowledge_base_matches"] if _passes_filters(c, min_experience, min_education)]

    if USE_DATABASE:
        _render_database_matches(results, min_experience, min_education)

    st.subheader("From your uploaded batch")
    if batch:
        for c in batch:
            skills = ", ".join(c.get("skills", [])[:12])
            st.markdown(f"**{c.get('name')}** · {c.get('experience_years', 0)} yrs")
            st.markdown(f'<span style="color:{MUTED};">{skills}</span>', unsafe_allow_html=True)
            st.write("")
    else:
        st.caption("No matches in the current upload batch.")

    st.subheader("From the knowledge base")
    if kb:
        for c in kb:
            skills = ", ".join(c.get("skills", [])[:12])
            st.markdown(f"**{c.get('name')}** · {c.get('similarity')}% match · _{c.get('source')}_")
            if skills:
                st.markdown(f'<span style="color:{MUTED};">{skills}</span>', unsafe_allow_html=True)
            st.write("")
    else:
        st.info("The knowledge base index hasn't been built yet. Run "
                "`python -m src.knowledge_base.dataset_loader` to index the "
                "Relational 54K, synthetic, and real-resume datasets for semantic search.")
