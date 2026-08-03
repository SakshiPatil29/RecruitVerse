"""Candidate Search — natural-language semantic search."""

import streamlit as st

from src.retrieval.search_candidates import semantic_search
from src.ui import state
from src.ui.theme import MUTED, page_title


def render():
    page_title("Candidate Search")
    st.caption("Search in natural language, e.g. \"Data Engineers with Spark\" or "
               "\"Python developers with Kafka\". Searches your uploaded batch and the "
               "dataset-backed knowledge base.")

    query = st.text_input("Search", placeholder="Find ML Engineers with AWS")
    if not query:
        return

    with st.spinner("Searching..."):
        results = semantic_search(query, session_candidates=state.get_resumes(), top_k=10)

    batch = results["uploaded_batch_matches"]
    kb = results["knowledge_base_matches"]

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
