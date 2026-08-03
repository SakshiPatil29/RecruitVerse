"""AI Insights — job-level AI helpers that aren't tied to one candidate."""

import streamlit as st

from src.ai import insights
from src.ai.ollama_client import is_available
from src.ui import state
from src.ui.theme import page_title


def render():
    page_title("AI Insights")

    online = is_available()
    if online:
        st.success("Ollama is connected — AI features use the live model.")
    else:
        st.info("Ollama isn't reachable. AI features still work using deterministic, "
                "rule-based fallbacks so the app remains fully functional.")

    jd = state.get_jd()
    if not jd:
        st.warning("Set a Job Description to unlock JD-level AI insights.")
        return

    st.subheader("Job description summary")
    if st.button("Summarize job description"):
        with st.spinner("Summarizing..."):
            st.session_state["_jd_summary"] = insights.generate_jd_summary(jd)
    if st.session_state.get("_jd_summary"):
        st.markdown(st.session_state["_jd_summary"])

    st.divider()
    ranked = state.get_ranked()
    if not ranked:
        st.caption("Rank candidates to generate top-candidate insights here.")
        return

    st.subheader("Top candidate at a glance")
    top = ranked[0]
    st.markdown(f"**{top.get('name')}** — {top.get('final_score')}% match")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Summarize top candidate"):
            with st.spinner("Summarizing..."):
                st.session_state["_top_summary"] = insights.generate_summary(top)
    with col2:
        if st.button("Recommend a decision"):
            with st.spinner("Assessing..."):
                st.session_state["_top_rec"] = insights.generate_hiring_recommendation(top)

    if st.session_state.get("_top_summary"):
        st.markdown("**Summary**")
        st.markdown(st.session_state["_top_summary"])
    if st.session_state.get("_top_rec"):
        st.markdown("**Recommendation**")
        st.markdown(st.session_state["_top_rec"])

    st.caption("For per-candidate summaries, questions, and improvement tips, open a "
               "candidate on the Candidate Details page.")
