import json
import os
import re
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

skills_file = os.path.join(
    BASE_DIR,
    "data",
    "skills_dictionary",
    "skills_dictionary.json"
)


def load_skills():

    with open(
        skills_file,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    all_skills = []

    for category in data.values():

        all_skills.extend(category)

    return all_skills


def extract_skills(text):

    skills_db = load_skills()

    found_skills = []

    text = text.lower()

    for skill in skills_db:

        pattern = r"\b" + re.escape(skill.lower()) + r"\b"

        if re.search(pattern, text):

            found_skills.append(skill)

    return list(
        set(found_skills)
    )