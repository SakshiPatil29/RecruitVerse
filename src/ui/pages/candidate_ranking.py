"""Candidate Ranking — run the deterministic pipeline, show ranked table + charts."""

import pandas as pd
import streamlit as st

from src.matching.embedding_matcher import semantic_backend
from src.pipeline.screening_pipeline import screen_candidates
from src.ranking.analytics import generate_analytics
from src.ui import state
from src.ui.theme import page_title


def _run_ranking():
    """Score the cohort. Returns None (after showing the error) if scoring
    fails, so a pipeline problem surfaces as a message instead of aborting
    the script and leaving the page blank."""

    jd = state.get_jd()
    resumes = state.get_resumes()
    try:
        with st.spinner("Scoring candidates against the job description..."):
            ranked = screen_candidates(jd, resumes)
    except Exception as exc:
        st.error(f"Ranking failed: {exc}")
        st.exception(exc)
        return None
    state.set_ranked(ranked)
    return ranked


def render():
    page_title("Candidate Ranking")

    jd = state.get_jd()
    resumes = state.get_resumes()

    if not jd:
        st.info("Set a Job Description first.")
        return
    if not resumes:
        st.info("Upload resumes first.")
        return

    ranked = state.get_ranked()
    col_a, col_b = st.columns([1, 3])
    with col_a:
        if st.button("Rank candidates", type="primary"):
            ranked = _run_ranking()
    if not ranked:
        ranked = _run_ranking()

    if not ranked:
        return

    st.caption(f"{len(ranked)} candidates ranked against **{jd.get('job_title', 'the role')}** "
               f"(50% skills · 30% semantic · 20% experience).")

    if semantic_backend() == "lexical":
        st.warning(
            "Semantic scores are using the lexical fallback — "
            "`sentence-transformers` isn't available, so the 30% semantic "
            "component is keyword-overlap rather than embeddings. "
            "Run `pip install sentence-transformers` for full-quality scoring."
        )

    table = pd.DataFrame([
        {
            "Rank": f"{c.get('medal', '')} {c['rank']}".strip(),
            "Candidate": c.get("name", "Unknown"),
            "Match Score": c["final_score"],
            "Skills": c["skill_score"],
            "Semantic": c["semantic_score"],
            "Experience": c.get("experience_years", 0),
        }
        for c in ranked
    ])

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Match Score": st.column_config.ProgressColumn(
                "Match Score", format="%d%%", min_value=0, max_value=100
            ),
            "Skills": st.column_config.NumberColumn("Skill %", format="%d%%"),
            "Semantic": st.column_config.NumberColumn("Semantic %", format="%d%%"),
            "Experience": st.column_config.NumberColumn("Exp (yrs)"),
        },
    )

    st.divider()
    names = [c.get("name", "Unknown") for c in ranked]
    picked = st.selectbox("Open a candidate's full profile", names)
    if st.button("View details"):
        chosen = next(c for c in ranked if c.get("name") == picked)
        st.session_state["selected_candidate"] = state.candidate_key(chosen)
        st.session_state["_nav"] = "Candidate Details"
        st.rerun()

    st.divider()
    st.subheader("Insights")
    analytics = generate_analytics(ranked)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Match score distribution**")
        dist = pd.DataFrame({"Candidate": names, "Score": [c["final_score"] for c in ranked]})
        st.bar_chart(dist.set_index("Candidate"))
    with c2:
        st.markdown("**Most common skill gaps**")
        if analytics["skill_gaps"]:
            gaps = pd.DataFrame(analytics["skill_gaps"], columns=["Skill", "Missing count"]).set_index("Skill")
            st.bar_chart(gaps)
        else:
            st.caption("No shared skill gaps across the cohort.")
