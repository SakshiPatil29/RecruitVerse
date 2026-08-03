"""Settings — inspect configuration and manage the knowledge base index."""

import os

import streamlit as st

from src.config.settings import (
    EMBEDDING_MODEL_NAME,
    KNOWLEDGE_BASE_INDEX_PATH,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    RANKING_WEIGHTS,
    USE_DATABASE,
)
from src.ai.ollama_client import is_available
from src.ui.theme import page_title


def render():
    page_title("Settings")

    st.subheader("Semantic matching")
    st.write(f"**Embedding model:** `{EMBEDDING_MODEL_NAME}`")
    st.caption("Set EMBEDDING_MODEL_NAME to swap in all-mpnet-base-v2 or BAAI/bge-small-en-v1.5.")

    st.subheader("Ranking weights")
    st.write(
        f"Skill match **{int(RANKING_WEIGHTS['skill_match']*100)}%** · "
        f"Semantic similarity **{int(RANKING_WEIGHTS['semantic_similarity']*100)}%** · "
        f"Experience **{int(RANKING_WEIGHTS['experience']*100)}%**"
    )

    st.subheader("Ollama (AI narrative only)")
    st.write(f"**Host:** `{OLLAMA_HOST}` · **Model:** `{OLLAMA_MODEL}`")
    st.write("**Status:** " + ("🟢 connected" if is_available() else "🔴 not reachable (fallbacks active)"))

    st.subheader("Database")
    st.write("**Persistence:** " + ("PostgreSQL enabled" if USE_DATABASE else "session-only (no database)"))
    st.caption("Set USE_DATABASE=true and DATABASE_URL to persist candidates and jobs.")

    st.divider()
    st.subheader("Knowledge base")
    exists = os.path.exists(KNOWLEDGE_BASE_INDEX_PATH)
    st.write("**Index status:** " + ("built" if exists else "not built"))
    st.caption("The knowledge base powers Candidate Search over the Relational 54K, synthetic, "
               "and real-resume datasets. Recruiters never browse these directly.")
    if st.button("Build / rebuild knowledge base index"):
        from src.knowledge_base.dataset_loader import build_index
        with st.spinner("Embedding dataset samples — this can take a while..."):
            records = build_index()
        if records:
            st.success(f"Indexed {len(records)} records.")
        else:
            st.warning("No dataset records found on disk. Place the datasets under data/imports "
                       "and data/raw_resumes, then rebuild.")
