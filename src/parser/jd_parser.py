"""
Job description parsing.

Reuses extract_education/extract_experience from resume_parser (a JD's
"5+ years experience" or "Bachelor's degree" phrasing is the same shape
as a resume's) and skill_extractor for the skill dictionary lookup. What's
new here is splitting skills into required vs preferred by looking for a
"preferred/nice to have/bonus" section, since the original parser lumped
every skill into one bucket.
"""

import json
import os

from src.matching.skill_extractor import extract_skills
from src.parser.file_extractor import extract_text
from src.parser.resume_parser import (
    extract_certifications,
    extract_education,
    extract_experience,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

JD_DIR = os.path.join(BASE_DIR, "data", "job_descriptions")
PARSED_JD_DIR = os.path.join(BASE_DIR, "data", "parsed_job_descriptions")

PREFERRED_MARKERS = [
    "preferred", "nice to have", "bonus", "good to have", "plus", "desirable",
]


def _split_required_preferred(text):
    """Return (required_text, preferred_text) by finding where a
    preferred/nice-to-have section starts. If no such section exists,
    everything is required."""

    lower = text.lower()
    earliest = None
    for marker in PREFERRED_MARKERS:
        idx = lower.find(marker)
        if idx != -1 and (earliest is None or idx < earliest):
            earliest = idx

    if earliest is None:
        return text, ""

    return text[:earliest], text[earliest:]


def parse_jd_text(text):
    required_text, preferred_text = _split_required_preferred(text)

    required_skills = extract_skills(required_text)
    preferred_skills = [s for s in extract_skills(preferred_text) if s not in required_skills]

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "skills": sorted(set(required_skills) | set(preferred_skills)),
        "education": extract_education(text),
        "experience_years": extract_experience(text),
        "certifications": extract_certifications(text),
        "raw_text": text,
    }


def parse_jd_file(file_path):
    with open(file_path, "rb") as file:
        file_bytes = file.read()
    text = extract_text(file_bytes, file_path)
    return parse_jd_text(text)


def parse_jd_upload(file_bytes, filename):
    """Parse an in-memory uploaded job description file."""
    text = extract_text(file_bytes, filename)
    return parse_jd_text(text)


def process_all_jds(input_folder=JD_DIR, output_folder=PARSED_JD_DIR):
    """Batch-parse every job description file into a structured JSON file.
    Returns the number of job descriptions processed."""

    os.makedirs(output_folder, exist_ok=True)
    count = 0

    for file in os.listdir(input_folder):
        if os.path.splitext(file)[1].lower() in (".txt", ".pdf", ".docx"):
            file_path = os.path.join(input_folder, file)
            result = parse_jd_file(file_path)

            output_file = os.path.join(output_folder, os.path.splitext(file)[0] + ".json")
            with open(output_file, "w", encoding="utf-8") as out:
                json.dump(result, out, indent=4)

            count += 1

    return count


if __name__ == "__main__":
    total = process_all_jds()
    print(f"Total JD JSON Files Created: {total}")
