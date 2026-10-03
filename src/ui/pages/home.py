"""Home — landing page shown first, before the Dashboard."""

import streamlit as st

from src.ui.theme import BLUE, GREEN, INK, NAVY, NAVY_SOFT, SLATE

_STEPS = [
    ("1", "Set up a Job Description", "Paste or upload the role you're hiring for."),
    ("2", "Upload Resumes", "Add 4–20 candidate resumes to screen."),
    ("3", "View Ranked Candidates", "See candidates scored and ranked by fit."),
    ("4", "Get AI Insights", "Read explainable, narrative summaries per candidate."),
]


def render():
    st.markdown(
        f"""<div style="text-align:center; padding: 0.5rem 0 2rem 0;">
            <div style="width:96px; height:96px; border-radius:22px; margin:0 auto 18px;
                        display:flex; align-items:center; justify-content:center;
                        background:linear-gradient(135deg, {NAVY} 0%, {NAVY_SOFT} 100%);
                        box-shadow:0 8px 20px -4px rgba(15,23,42,0.35);">
                <svg viewBox="0 0 24 24" width="56" height="56" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="9" cy="8" r="3" fill="#7dd3fc"/>
                    <path d="M9 12c-3.3 0-6 2.2-6 5v2h11v-2c0-2.8-2.4-5-5-5z" fill="#7dd3fc"/>
                    <circle cx="15.5" cy="10.2" r="2.6" fill="#3b82f6"/>
                    <path d="M15.5 13.4c-2.8 0-5.2 1.9-5.2 4.3v1.3h10.4v-1.3c0-2.4-2.4-4.3-5.2-4.3z" fill="#3b82f6"/>
                    <path d="M14 9.5l4.5-4.5m0 0h-3.2m3.2 0v3.2" stroke="{GREEN}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div style="font-size:40px; font-weight:800; color:{INK}; letter-spacing:-0.01em;">
                Recruit<span style="color:{BLUE};">Verse</span>
            </div>
            <div style="font-size:22px; font-weight:700; color:{INK}; margin-top:14px;">
                AI-Powered Resume Screening &amp; Candidate Ranking
            </div>
            <div style="font-size:15px; color:{SLATE}; max-width:620px; margin:10px auto 0; line-height:1.6;">
                Upload a job description and a batch of resumes, and RecruitVerse parses,
                semantically matches, and ranks your candidates &mdash; with explainable,
                transparent scores for every match.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("#### How it works")
    cols = st.columns(4, gap="medium")
    for col, (num, title, desc) in zip(cols, _STEPS):
        with col:
            st.markdown(
                f"""<div class="ats-card" style="text-align:center;">
                    <div style="width:34px; height:34px; border-radius:50%; margin:0 auto 12px;
                                background:{BLUE}; color:#ffffff; font-weight:800;
                                display:flex; align-items:center; justify-content:center;">{num}</div>
                    <div style="font-weight:700; color:{INK}; margin-bottom:6px;">{title}</div>
                    <div style="font-size:13px; color:{SLATE};">{desc}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.write("")
    st.write("")
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        if st.button("Get Started →", use_container_width=True, type="primary"):
            st.session_state["_nav"] = "Job Description"
            st.rerun()
