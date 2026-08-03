"""
Backend knowledge base built from the project's existing datasets
(Relational 54K, Synthetic Resume Dataset, LiveCareer/"real" resumes).

Per the spec, recruiters never interact with these datasets directly —
they exist purely so Candidate Search (src/ui/pages/candidate_search.py)
can run natural-language semantic search over a large corpus even when
the recruiter has only uploaded a handful of resumes for the active JD.

Building the index embeds text with the same deterministic embedding
model used everywhere else (src/matching/embedding_matcher) — Ollama is
never involved here either. Because these datasets are large (tens of
thousands of resumes), build_index samples a bounded number of rows per
source (settings.KNOWLEDGE_BASE_SAMPLE_SIZE) rather than embedding all of
them, and caches the result to disk so it only has to run once.

This is an offline/background step (`python -m src.knowledge_base.dataset_loader`),
not something that runs on every app startup.
"""

import os
import pickle
import random

from src.config.settings import (
    DATASET_SOURCES,
    KNOWLEDGE_BASE_DIR,
    KNOWLEDGE_BASE_INDEX_PATH,
    KNOWLEDGE_BASE_SAMPLE_SIZE,
)
from src.matching.skill_extractor import extract_skills


def _load_relational_54k(sample_size):
    """01_people.csv + 05_person_skills.csv -> one lightweight
    pseudo-resume text per person, built from their skill list (this
    dataset has no free-text resume body)."""

    import pandas as pd

    base = DATASET_SOURCES["relational_54k"]
    people_path = os.path.join(base, "01_people.csv")
    skills_path = os.path.join(base, "05_person_skills.csv")

    if not (os.path.exists(people_path) and os.path.exists(skills_path)):
        return []

    people = pd.read_csv(people_path)
    skills = pd.read_csv(skills_path)

    if len(people) > sample_size:
        people = people.sample(sample_size, random_state=42)

    skills_by_person = skills.groupby("person_id")["skill"].apply(list).to_dict()

    records = []
    for _, row in people.iterrows():
        person_id = row["person_id"]
        skill_list = skills_by_person.get(person_id, [])
        if not skill_list:
            continue
        text = f"{row.get('name', '')}. Skills: {', '.join(skill_list)}."
        records.append({
            "source": "relational_54k",
            "candidate_id": f"r54k_{person_id}",
            "name": row.get("name", "Unknown"),
            "text": text,
            "skills": skill_list,
        })
    return records


def _load_livecareer(sample_size):
    """dataset 1/Resume/Resume.csv -> (ID, Resume_str, Category)."""

    import pandas as pd

    base = DATASET_SOURCES["real"]
    csv_path = os.path.join(base, "dataset 1", "Resume", "Resume.csv")
    if not os.path.exists(csv_path):
        return []

    df = pd.read_csv(csv_path)
    if len(df) > sample_size:
        df = df.sample(sample_size, random_state=42)

    records = []
    text_col = "Resume_str" if "Resume_str" in df.columns else df.columns[1]
    for _, row in df.iterrows():
        text = str(row.get(text_col, ""))[:3000]
        if not text.strip():
            continue
        records.append({
            "source": "livecareer",
            "candidate_id": f"lc_{row.get('ID', len(records))}",
            "name": row.get("Category", "Unknown Category"),
            "text": text,
            "skills": extract_skills(text),
        })
    return records


def _load_synthetic(sample_size):
    """synthetic_10000/.../resumes_txt/*.txt -> one record per file."""

    base = DATASET_SOURCES["synthetic"]

    # Prefer a dedicated resumes_txt directory (the synthetic corpus layout);
    # fall back to the first directory that actually holds many .txt files so
    # we don't accidentally latch onto a stray README.txt in another folder.
    txt_dir = None
    best_count = 0
    for root, _dirs, files in os.walk(base):
        txt_here = [f for f in files if f.endswith(".txt")]
        if os.path.basename(root) == "resumes_txt" and txt_here:
            txt_dir = root
            break
        if len(txt_here) > best_count:
            best_count = len(txt_here)
            txt_dir = root

    if not txt_dir:
        return []

    files = [f for f in os.listdir(txt_dir) if f.endswith(".txt")]
    random.Random(42).shuffle(files)
    files = files[:sample_size]

    records = []
    for file in files:
        with open(os.path.join(txt_dir, file), "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        records.append({
            "source": "synthetic",
            "candidate_id": f"syn_{os.path.splitext(file)[0]}",
            "name": os.path.splitext(file)[0],
            "text": text[:3000],
            "skills": extract_skills(text),
        })
    return records


def build_index(sample_size=None, save=True):
    """Embed a sample of each dataset and save the combined index to disk.
    Returns the list of records (each with an added 'embedding' key)."""

    from src.matching.embedding_matcher import embed_texts

    sample_size = sample_size or KNOWLEDGE_BASE_SAMPLE_SIZE

    records = []
    for loader in (_load_relational_54k, _load_livecareer, _load_synthetic):
        try:
            records.extend(loader(sample_size))
        except Exception as exc:  # dataset optional / not present on disk
            print(f"[knowledge_base] skipped a source: {exc}")

    if not records:
        print("[knowledge_base] no dataset records found — nothing to index.")
        return []

    texts = [r["text"] for r in records]
    embeddings = embed_texts(texts)
    for record, vector in zip(records, embeddings):
        record["embedding"] = vector

    if save:
        os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
        with open(KNOWLEDGE_BASE_INDEX_PATH, "wb") as fh:
            pickle.dump(records, fh)
        print(f"[knowledge_base] indexed {len(records)} records -> {KNOWLEDGE_BASE_INDEX_PATH}")

    return records


def load_index():
    if not os.path.exists(KNOWLEDGE_BASE_INDEX_PATH):
        return []
    with open(KNOWLEDGE_BASE_INDEX_PATH, "rb") as fh:
        return pickle.load(fh)


def semantic_search(query, top_k=10):
    """Natural-language search over the knowledge base index. Returns the
    top_k records (without the raw embedding vector) sorted by similarity.
    Returns [] if the index hasn't been built yet."""

    from src.matching.embedding_matcher import cosine_similarity, embed_text

    records = load_index()
    if not records:
        return []

    query_vec = embed_text(query)
    scored = []
    for record in records:
        similarity = cosine_similarity(query_vec, record["embedding"])
        scored.append((similarity, record))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    results = []
    for similarity, record in scored[:top_k]:
        clean = {k: v for k, v in record.items() if k != "embedding"}
        clean["similarity"] = round(similarity * 100, 2)
        results.append(clean)
    return results


if __name__ == "__main__":
    build_index()
