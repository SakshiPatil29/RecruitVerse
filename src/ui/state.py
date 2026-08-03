"""
Session state helpers.

The ATS workflow spans several pages (upload JD -> upload resumes -> rank
-> details -> AI insights), and Streamlit reruns the whole script on every
interaction, so the working set (active JD, parsed resumes, ranked
results) lives in st.session_state. This keeps the app fully functional
with no database — persistence to Postgres is optional and additive.
"""

import streamlit as st

_DEFAULTS = {
    "jd": None,                 # parsed job description dict
    "resumes": [],             # list of parsed resume dicts
    "ranked": [],              # list of ranked candidate dicts
    "selected_candidate": None,  # source_filename of candidate open in Details
    "ai_cache": {},            # {(candidate_key, feature): text} to avoid re-calling Ollama
}


def init_state():
    for key, default in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default() if callable(default) else default


def set_jd(jd):
    st.session_state["jd"] = jd


def get_jd():
    return st.session_state.get("jd")


def set_resumes(resumes):
    st.session_state["resumes"] = resumes


def get_resumes():
    return st.session_state.get("resumes", [])


def set_ranked(ranked):
    st.session_state["ranked"] = ranked


def get_ranked():
    return st.session_state.get("ranked", [])


def candidate_key(candidate):
    return candidate.get("source_filename") or candidate.get("name") or str(id(candidate))


def cache_ai(candidate, feature, text):
    st.session_state["ai_cache"][(candidate_key(candidate), feature)] = text


def get_cached_ai(candidate, feature):
    return st.session_state["ai_cache"].get((candidate_key(candidate), feature))
