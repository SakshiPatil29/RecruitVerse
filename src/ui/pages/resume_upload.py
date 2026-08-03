"""Resume Upload — upload 4–20 resumes, parse each, show status."""

import pandas as pd
import streamlit as st

from src.parser.resume_parser import parse_resume_upload
from src.ui import state
from src.ui.theme import page_title


def render():
    page_title("Resume Upload")
    st.caption("Upload multiple resumes (PDF, DOCX, or TXT). Each is parsed automatically.")

    uploaded = st.file_uploader(
        "Drag & drop resumes here",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="resume_files",
    )

    if uploaded and st.button("Parse resumes", type="primary"):
        parsed_resumes = []
        progress = st.progress(0.0, text="Parsing resumes...")
        rows = []

        for i, file in enumerate(uploaded, start=1):
            try:
                result = parse_resume_upload(file.getvalue(), file.name)
                parsed_resumes.append(result)
                rows.append({
                    "File": file.name,
                    "Candidate": result.get("name"),
                    "Skills found": len(result.get("skills", [])),
                    "Experience": f"{result.get('experience_years', 0)} yrs",
                    "Status": "Parsed",
                })
            except Exception as exc:
                rows.append({
                    "File": file.name,
                    "Candidate": "—",
                    "Skills found": 0,
                    "Experience": "—",
                    "Status": f"Failed: {exc}",
                })
            progress.progress(i / len(uploaded), text=f"Parsed {i}/{len(uploaded)}")

        progress.empty()
        state.set_resumes(parsed_resumes)
        state.set_ranked([])  # new upload set invalidates old ranking
        st.session_state["_upload_rows"] = rows

    rows = st.session_state.get("_upload_rows")
    resumes = state.get_resumes()

    if rows:
        st.subheader("Parsing results")
        st.table(pd.DataFrame(rows).style.hide(axis="index"))

    if resumes:
        count = len(resumes)
        if count < 4:
            st.warning(f"{count} resume(s) uploaded. The workflow is designed for 4–20 at a time, but you can still rank.")
        elif count > 20:
            st.warning(f"{count} resumes uploaded — more than the recommended 20. Ranking may be slower.")
        else:
            st.markdown(
                f'<div class="ats-success-banner">✅ {count} resumes parsed and ready.</div>',
                unsafe_allow_html=True,
            )

        if state.get_jd():
            st.info("Job description is set. Head to Candidate Ranking to score these candidates.")
        else:
            st.info("Next: set a Job Description so candidates can be scored against it.")
