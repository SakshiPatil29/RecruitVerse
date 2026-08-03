"""
Resume parsing.

The extraction primitives below (extract_email, extract_phone,
extract_name, extract_education, extract_experience) are kept from the
original implementation — they worked fine on plain text and several
other modules (src/parser/jd_parser.py, tests) import them directly.
This version adds the fields the ATS spec needs that the original parser
didn't cover (certifications, projects, previous companies, summary) and
routes every format through file_extractor.extract_text instead of only
accepting raw .txt.
"""

import datetime
import json
import os
import re

from src.matching.skill_extractor import extract_skills
from src.parser.file_extractor import extract_text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW_TEXT_DIR = os.path.join(BASE_DIR, "data", "parsed_resumes", "raw_text")
PARSED_JSON_DIR = os.path.join(BASE_DIR, "data", "parsed_resumes", "parsed_json")

EDUCATION_KEYWORDS = [
    "B.Tech", "B.E", "B.Sc", "BCA", "MCA", "MBA", "BBA",
    "M.Tech", "M.Sc", "PhD", "Bachelor", "Master", "B.Com", "M.Com", "B.A", "M.A",
]

CERTIFICATION_KEYWORDS = [
    "AWS Certified", "Azure Certified", "Google Cloud Certified", "PMP",
    "Scrum Master", "CSM", "CKA", "CKAD", "Certified Kubernetes",
    "Databricks Certified", "Snowflake Certified", "Six Sigma",
    "CompTIA", "CISSP", "CFA", "Salesforce Certified",
]

SECTION_HEADERS = {
    "experience": ["experience", "work experience", "employment history", "professional experience"],
    "projects": ["projects", "project experience", "academic projects"],
    "certifications": ["certifications", "certificates", "licenses"],
    "summary": ["summary", "profile", "objective", "about me"],
}


def extract_email(text):
    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    match = re.search(pattern, text)
    return match.group() if match else None


def extract_phone(text):
    pattern = r"(\+?\d[\d\-\s]{8,15}\d)"
    match = re.search(pattern, text)
    return match.group() if match else None


NAME_SKIP_LINES = {
    "contact", "contact information", "contact info", "contact details",
    "resume", "curriculum vitae", "cv",
    "personal information", "personal details", "personal info",
    "profile", "objective", "career objective",
    "summary", "professional summary", "about me",
}

_PHONE_ONLY_PATTERN = re.compile(r"^[\d\s\-\+\(\)]{7,}$")
_CONTACT_LABEL_PATTERN = re.compile(r"^(email|phone|tel|mobile|contact)\s*:", re.IGNORECASE)


def extract_name(text):
    lines = text.split("\n")
    for line in lines[:10]:
        line = line.strip()
        if not (3 < len(line) < 50):
            continue
        if "@" in line or _PHONE_ONLY_PATTERN.match(line) or _CONTACT_LABEL_PATTERN.match(line):
            continue
        if line.strip(":# -").lower() in NAME_SKIP_LINES:
            continue
        return line
    return "Unknown"


def extract_education(text):
    text_lower = text.lower()
    for edu in EDUCATION_KEYWORDS:
        pattern = r"\b" + re.escape(edu.lower()) + r"\b"
        if re.search(pattern, text_lower):
            return edu
    return None


EXPERIENCE_PHRASE_PATTERN = re.compile(r"(\d+)\+?\s*(?:years?|yrs?\.?)\b", re.IGNORECASE)

_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+"
DATE_RANGE_PATTERN = re.compile(
    r"(?:" + _MONTH + r")?(\d{4})\s*(?:-|–|—|to)\s*(?:" + _MONTH + r")?(present|current|now|\d{4})",
    re.IGNORECASE,
)


def _experience_from_date_ranges(text):
    """Fallback for resumes that list job date ranges (e.g. '2019 - Present')
    but never spell out a total, which is the common case in practice."""

    section = _find_section(text, SECTION_HEADERS["experience"]) or text
    current_year = datetime.date.today().year

    starts, ends = [], []
    for start_str, end_str in DATE_RANGE_PATTERN.findall(section):
        start_year = int(start_str)
        end_year = current_year if end_str.lower() in ("present", "current", "now") else int(end_str)
        if start_year > current_year or end_year < start_year:
            continue
        starts.append(start_year)
        ends.append(end_year)

    if not starts:
        return 0
    return max(ends) - min(starts)


def extract_experience(text):
    matches = EXPERIENCE_PHRASE_PATTERN.findall(text)
    if matches:
        return max(int(x) for x in matches)
    return _experience_from_date_ranges(text)


def extract_certifications(text):
    found = []
    text_lower = text.lower()
    for cert in CERTIFICATION_KEYWORDS:
        if cert.lower() in text_lower:
            found.append(cert)
    return found


def _find_section(text, header_names):
    """Return the text of a named section (until the next known section
    heading), or None if not found. Resumes have no consistent structure,
    so this is intentionally forgiving rather than a strict parser."""

    lines = text.split("\n")
    lower_lines = [line.strip().lower() for line in lines]
    all_headers = sum(SECTION_HEADERS.values(), [])

    start = None
    for i, line in enumerate(lower_lines):
        clean = line.strip(":# -")
        if clean in header_names:
            start = i + 1
            break

    if start is None:
        return None

    end = len(lines)
    for i in range(start, len(lines)):
        clean = lower_lines[i].strip(":# -")
        if clean and clean in all_headers and clean not in header_names:
            end = i
            break

    section_text = "\n".join(lines[start:end]).strip()
    return section_text or None


def extract_projects(text):
    section = _find_section(text, SECTION_HEADERS["projects"])
    if not section:
        return []

    projects = []
    for line in section.split("\n"):
        line = line.strip("-•* \t")
        if len(line) > 4:
            projects.append(line)
    return projects[:10]


def extract_previous_companies(text):
    """Best-effort: pull lines from the experience section that look like
    'Role, Company' or 'Company — Role' rather than building a full NER
    pipeline for company names."""

    section = _find_section(text, SECTION_HEADERS["experience"])
    if not section:
        return []

    companies = []
    for line in section.split("\n")[:20]:
        line = line.strip("-•* \t")
        if any(sep in line for sep in [",", "–", "—", "|", " at "]) and 3 < len(line) < 100:
            companies.append(line)
    return companies[:10]


def build_summary(text, skills, experience_years):
    """A short, non-AI fallback summary. The richer AI-generated summary
    (src/ai/insights.generate_summary) is preferred when Ollama is
    available; this keeps the app useful without it."""

    section = _find_section(text, SECTION_HEADERS["summary"])
    if section:
        return " ".join(section.split())[:400]

    top_skills = ", ".join(skills[:5]) if skills else "no listed skills"
    return f"{experience_years} years of experience. Key skills: {top_skills}."


def parse_resume_text(text):
    """Parse raw resume text into a structured candidate dict."""
    skills = extract_skills(text)
    experience_years = extract_experience(text)

    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": skills,
        "education": extract_education(text),
        "experience_years": experience_years,
        "certifications": extract_certifications(text),
        "projects": extract_projects(text),
        "previous_companies": extract_previous_companies(text),
        "summary": build_summary(text, skills, experience_years),
        "raw_text": text,
    }


def parse_resume_file(file_path):
    """Parse a resume from disk (any supported format)."""
    with open(file_path, "rb") as file:
        file_bytes = file.read()
    text = extract_text(file_bytes, file_path)
    return parse_resume_text(text)


def parse_resume_upload(file_bytes, filename):
    """Parse an in-memory uploaded resume (Streamlit UploadedFile.getvalue()
    bytes + its name). This is the entry point the ATS UI uses."""
    text = extract_text(file_bytes, filename)
    result = parse_resume_text(text)
    result["source_filename"] = filename
    return result


def _log_to_catalog(file_name, output_file):
    """Best-effort data lake catalog logging. Never blocks parsing if the
    database isn't reachable (e.g. running the parser standalone)."""
    try:
        from src.config.settings import USE_DATABASE

        if not USE_DATABASE:
            return

        from src.config.db import get_connection

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO lake_catalog(file_name, file_type, location, created_at) VALUES (%s, %s, %s, now())",
            (file_name, "resume_json", output_file),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass


def process_all_resumes(input_folder=RAW_TEXT_DIR, output_folder=PARSED_JSON_DIR, log_to_catalog=True):
    """Batch-parse every resume file in input_folder into a structured JSON
    file in output_folder. Returns the number of resumes processed."""

    os.makedirs(output_folder, exist_ok=True)
    count = 0

    for file in os.listdir(input_folder):
        if os.path.splitext(file)[1].lower() in (".txt", ".pdf", ".docx"):
            file_path = os.path.join(input_folder, file)
            result = parse_resume_file(file_path)

            output_file = os.path.join(output_folder, os.path.splitext(file)[0] + ".json")
            with open(output_file, "w", encoding="utf-8") as out:
                json.dump(result, out, indent=4)

            if log_to_catalog:
                _log_to_catalog(file, output_file)

            count += 1

    return count


if __name__ == "__main__":
    total = process_all_resumes()
    print(f"Total JSON Files Created: {total}")
