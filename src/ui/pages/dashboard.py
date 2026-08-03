"""Dashboard — at-a-glance status of the current screening session."""

import streamlit as st

from src.ranking.analytics import generate_analytics
from src.ui import state
from src.ui.theme import (
    AMBER,
    BLUE,
    BRONZE,
    GOLD,
    GREEN,
    INK,
    MUTED,
    RED,
    SILVER,
    donut_chart,
    legend_row,
    metric_card,
    page_title,
    rank_row,
    score_color,
    summary_chip,
)

# Score bands for the distribution donut — thresholds match score_color()
# so a candidate's band always agrees with their score's color elsewhere.
_BANDS = [
    ("Strong", 85, GREEN),
    ("Good", 70, BLUE),
    ("Moderate", 50, AMBER),
    ("Low", 0, RED),
]

_MEDAL_COLORS = {1: GOLD, 2: SILVER, 3: BRONZE}
_MEDAL_DEFAULT = MUTED

_SAMPLE_RANKED = [
    {"name": "Candidate A", "final_score": 88},
    {"name": "Candidate B", "final_score": 76},
    {"name": "Candidate C", "final_score": 68},
    {"name": "Candidate D", "final_score": 61},
    {"name": "Candidate E", "final_score": 42},
]


def _band_for(score):
    for label, threshold, _ in _BANDS:
        if score >= threshold:
            return label
    return "Low"


def _band_counts(candidates):
    counts = {label: 0 for label, _, _ in _BANDS}
    for c in candidates:
        counts[_band_for(c["final_score"])] += 1
    return counts


def render():
    jd = state.get_jd()
    resumes = state.get_resumes()
    ranked = state.get_ranked()

    header_col, chip_col = st.columns([3, 1])
    with header_col:
        page_title("Dashboard")
        st.caption("Overview of your current screening session.")
    with chip_col:
        job_label = jd.get("job_title") if jd else "No active job"
        summary_chip(f"💼 {job_label} &nbsp;·&nbsp; 👥 {len(resumes)} candidates")

    st.write("")

    analytics = generate_analytics(ranked)
    top = ranked[0] if ranked else None
    avg_score = analytics["avg_score"]

    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        metric_card("Uploaded Resumes", len(resumes), color=BLUE, icon="📂",
                    descriptor="Ready for screening")
    with col2:
        metric_card("Parsed Resumes", len(resumes), color=BLUE, icon="📄",
                    descriptor="Successfully parsed")
    with col3:
        score_clr = score_color(avg_score) if ranked else INK
        metric_card("Average Match Score", f"{avg_score}%" if ranked else "—", color=score_clr, icon="📊",
                    descriptor="Across ranked candidates")

    st.write("")
    col4, col5 = st.columns(2, gap="medium")
    with col4:
        metric_card("Latest Job Description", jd.get("job_title", "Active JD") if jd else "None yet",
                    color=BLUE if jd else INK, icon="🧾", descriptor="Currently active role")
    with col5:
        metric_card("Top Ranked Candidate", top.get("name") if top else "None yet",
                    color=BLUE if top else INK, icon="🏆", descriptor="Highest match score")

    st.write("")
    st.subheader("Quick actions")
    qa1, qa2, qa3 = st.columns(3, gap="medium")
    with qa1:
        if st.button("Set up Job Description", use_container_width=True):
            st.session_state["_nav"] = "Job Description"
            st.rerun()
    with qa2:
        if st.button("Upload Resumes", use_container_width=True):
            st.session_state["_nav"] = "Resume Upload"
            st.rerun()
    with qa3:
        if st.button("View Ranking", use_container_width=True):
            st.session_state["_nav"] = "Candidate Ranking"
            st.rerun()

    if not jd and not resumes:
        st.write("")
        st.info("Start by setting up a Job Description, then upload 4–20 resumes to rank candidates.")

    st.write("")
    st.divider()

    is_sample = not ranked
    display_ranked = ranked if ranked else _SAMPLE_RANKED
    top5 = sorted(display_ranked, key=lambda c: c["final_score"], reverse=True)[:5]
    bands = _band_counts(display_ranked)
    segments = [(label, bands[label], color) for label, _, color in _BANDS]

    panel_left, panel_right = st.columns([3, 2], gap="medium")
    with panel_left:
        with st.container(border=True):
            st.markdown("#### Top Candidates")
            if is_sample:
                st.caption("Sample preview — rank candidates to see real results here.")
            for i, c in enumerate(top5, start=1):
                rank_row(i, c.get("name", "Unknown"), c["final_score"], _MEDAL_COLORS.get(i, _MEDAL_DEFAULT))

    with panel_right:
        with st.container(border=True):
            st.markdown("#### Score Distribution")
            if is_sample:
                st.caption("Sample preview")
            donut_chart(segments, center_value=len(display_ranked), center_label="Candidates")
            for label, count, color in segments:
                legend_row(label, count, color)
