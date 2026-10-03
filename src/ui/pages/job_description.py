"""Job Description — paste or upload a JD, extract structured requirements."""

import streamlit as st

from src.parser.jd_parser import parse_jd_text, parse_jd_upload
from src.ui import state
from src.ui.theme import page_title, requirement_summary_card, skill_tags


def render():
    page_title("Job Description")
    st.caption("Paste or upload the role you're hiring for. We'll extract the requirements before matching.")

    job_title = st.text_input(
        "Job title",
        value=(state.get_jd() or {}).get("job_title", ""),
        key="jd_job_title",
    )

    tab_paste, tab_upload = st.tabs(["Paste text", "Upload file"])
    parsed = None

    with tab_paste:
        text = st.text_area("Job description", height=260, placeholder="Paste the full job description here...")
        if st.button("Extract requirements", key="jd_paste_btn"):
            if text.strip():
                parsed = parse_jd_text(text)
            else:
                st.warning("Paste a job description first.")

    with tab_upload:
        uploaded = st.file_uploader("Upload JD (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="jd_file")
        if uploaded is not None and st.button("Extract requirements", key="jd_upload_btn"):
            try:
                parsed = parse_jd_upload(uploaded.getvalue(), uploaded.name)
            except ValueError as exc:
                st.error(str(exc))

    if parsed is not None:
        parsed["job_title"] = job_title.strip() or "Untitled role"
        state.set_jd(parsed)
        # A new JD invalidates any previous ranking.
        state.set_ranked([])

    jd = state.get_jd()
    if not jd:
        st.info("No job description set yet.")
        return

    st.divider()
    st.subheader(f"Extracted requirements — {jd.get('job_title', 'Active JD')}")

    st.markdown("**Required skills**")
    skill_tags(jd.get("required_skills", []))

    st.markdown("**Preferred skills**")
    skill_tags(jd.get("preferred_skills", []))

    st.write("")
    requirement_summary_card([
        ("Experience required", f"{jd.get('experience_years', 0)}+ yrs"),
        ("Education", jd.get("education") or "—"),
        ("Certifications", ", ".join(jd.get("certifications", [])) or "—"),
    ])

    if state.get_resumes():
        st.success("Job description ready. Head to Candidate Ranking to score your uploaded resumes.")
    else:
        st.info("Next: upload resumes on the Resume Upload page.")
