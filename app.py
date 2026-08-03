"""
RecruitVerse ATS — Streamlit entrypoint.

Thin router: it sets up the theme and session state, renders the sidebar,
and delegates each page to its module in src/ui/pages/. All real logic
lives in src/ (pipeline, matching, ai) so the UI stays a presentation
layer.
"""

from src.config.runtime import preload_torch

# Must run before any module that imports pandas (i.e. before the page
# imports below) or torch's DLLs fail to initialise on Windows and semantic
# scoring silently degrades. See src/config/runtime.py for the details.
preload_torch()

import streamlit as st  # noqa: E402

from src.ui import state  # noqa: E402
from src.ui.pages import (  # noqa: E402
    ai_insights,
    candidate_details,
    candidate_ranking,
    candidate_search,
    dashboard,
    job_description,
    resume_upload,
    settings,
)
from src.ui.theme import inject_theme  # noqa: E402

st.set_page_config(page_title="RecruitVerse ATS", page_icon="🧭", layout="wide")

inject_theme()
state.init_state()

PAGES = {
    "🏠 Dashboard": dashboard.render,
    "📄 Job Description": job_description.render,
    "📂 Resume Upload": resume_upload.render,
    "🏆 Candidate Ranking": candidate_ranking.render,
    "👤 Candidate Details": candidate_details.render,
    "🔍 Candidate Search": candidate_search.render,
    "🤖 AI Insights": ai_insights.render,
    "⚙️ Settings": settings.render,
}

# Map the plain nav labels used by quick-action buttons to sidebar keys.
_ALIASES = {
    "Job Description": "📄 Job Description",
    "Resume Upload": "📂 Resume Upload",
    "Candidate Ranking": "🏆 Candidate Ranking",
    "Candidate Details": "👤 Candidate Details",
}

st.sidebar.markdown(
    """<div class="ats-brand">
        <div class="ats-brand-badge">🧭</div>
        <div>
            <div class="ats-brand-name">RecruitVerse</div>
            <div class="ats-brand-tag">AI Resume Screening &amp; Ranking</div>
        </div>
    </div>""",
    unsafe_allow_html=True,
)

# Honor programmatic navigation requests (quick-action buttons) once.
default_index = 0
if "_nav" in st.session_state:
    target = _ALIASES.get(st.session_state.pop("_nav"))
    if target in PAGES:
        default_index = list(PAGES).index(target)

choice = st.sidebar.radio("Navigate", list(PAGES.keys()), index=default_index)

# Reserve the status slot now so it keeps its place under the nav, but fill
# it after the page has run — the page is what sets the JD / resumes /
# ranking, and writing the caption first would report the previous run's
# counts (e.g. "Resumes: 0" on the very rerun that parsed them).
st.sidebar.divider()
status_slot = st.sidebar.empty()

PAGES[choice]()

status_slot.caption(
    f"JD: {'✅ set' if state.get_jd() else '—'}  ·  "
    f"Resumes: {len(state.get_resumes())}  ·  "
    f"Ranked: {len(state.get_ranked())}"
)
