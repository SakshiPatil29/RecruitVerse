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
from src.parser.file_extractor import extract_tables, extract_text

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
    "experience": ["experience", "work experience", "employment history", "professional experience", "work details"],
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
    "basic information", "basic info", "basic details",
    "contact", "contact information", "contact info", "contact details",
    "resume", "curriculum vitae", "cv",
    "personal information", "personal details", "personal info",
    "profile", "objective", "career objective",
    "summary", "professional summary", "about me",
}

# Single words that show up as flattened table headers/labels (e.g. a
# "Personal Details" table's header row reads as "Name Email Phone
# Address" once linearized) rather than as part of an actual name. A line
# made up entirely of these is a label row, never a name — see
# _looks_like_name.
_FIELD_LABEL_WORDS = {
    "name", "email", "phone", "mobile", "address", "dob", "gender",
    "nationality", "marital", "status", "contact", "date", "birth",
    "tel", "telephone", "fax", "father", "mother", "candidate", "full",
    "details", "information", "personal", "employee", "id", "no",
}

_PHONE_ONLY_PATTERN = re.compile(r"^[\d\s\-\+\(\)]{7,}$")
_CONTACT_LABEL_PATTERN = re.compile(r"^(email|phone|tel|mobile|contact)\s*:", re.IGNORECASE)
_URL_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|\b[a-z0-9-]+\.(?:com|net|org|io|co|in)\b)", re.IGNORECASE
)
_NAME_WORD_PATTERN = re.compile(r"^[A-Za-z][A-Za-z'.-]*$")

# Labels that mark a cell as holding a candidate's name, for the
# table-based extraction path (_name_from_tables). Matched case-
# insensitively against a cell stripped of ":" / whitespace.
_NAME_LABEL_PATTERN = re.compile(
    r"^(full\s*name|candidate\s*name|employee\s*name|applicant\s*name|name)$",
    re.IGNORECASE,
)


def _looks_like_name(line):
    words = line.split()
    if not (2 <= len(words) <= 4):
        return False
    if not all(_NAME_WORD_PATTERN.match(word) for word in words):
        return False
    # Reject a flattened label/header row (e.g. "Name Email Phone
    # Address") that happens to satisfy the word-count/alphabetic checks
    # above just as well as a real name would.
    if all(word.lower().strip(".") in _FIELD_LABEL_WORDS for word in words):
        return False
    letters = sum(ch.isalpha() for ch in line)
    non_space = sum(not ch.isspace() for ch in line)
    return non_space > 0 and letters / non_space >= 0.8


def _name_from_tables(tables):
    """Look for a candidate's name inside structured table cells before
    ever falling back to guessing from linearized text. Handles the two
    layouts resumes actually use:

    1. Label/value pairs in the same row, e.g. a row ["Name", "John Doe"]
       or ["Name:", "John Doe"] — common in a vertical "Personal Details"
       table.
    2. A header row followed by a data row, e.g. header
       ["Name", "Email", "Phone"] then data ["John Doe", "j@x.com", ...]
       — the same shape extract_experience's Work Details table reading
       already relies on for From/To columns.

    Returns None (not "Unknown") if no table has a recognizable name
    cell, so the caller falls through to the text heuristic exactly like
    extract_experience falls through to date-range/phrase extraction.
    """

    if not tables:
        return None

    for table in tables:
        for r_idx, row in enumerate(table):
            cells = [(cell or "").strip() for cell in row]

            for c_idx, cell in enumerate(cells):
                if not _NAME_LABEL_PATTERN.match(cell.strip(":")):
                    continue

                # Layout 1: value is another cell in the same row.
                for other in cells[c_idx + 1:] + cells[:c_idx]:
                    if other and _looks_like_name(other):
                        return other

                # Layout 2: this is a header cell; the value sits in the
                # same column of the very next row.
                if r_idx + 1 < len(table):
                    next_row = [(c or "").strip() for c in table[r_idx + 1]]
                    if c_idx < len(next_row) and _looks_like_name(next_row[c_idx]):
                        return next_row[c_idx]

    return None


def extract_name(text, tables=None):
    from_table = _name_from_tables(tables)
    if from_table:
        return from_table

    lines = text.split("\n")
    for line in lines[:10]:
        line = line.strip()
        if not (3 < len(line) < 50):
            continue
        if "@" in line or _PHONE_ONLY_PATTERN.match(line) or _CONTACT_LABEL_PATTERN.match(line):
            continue
        if _URL_PATTERN.search(line):
            continue
        cleaned = line.strip(":# -")
        if cleaned.lower() in NAME_SKIP_LINES:
            continue
        if _looks_like_name(cleaned):
            return cleaned
    return "Unknown"


def extract_education(text):
    text_lower = text.lower()
    for edu in EDUCATION_KEYWORDS:
        pattern = r"\b" + re.escape(edu.lower()) + r"\b"
        if re.search(pattern, text_lower):
            return edu
    return None


EXPERIENCE_PHRASE_PATTERN = re.compile(r"(\d+)\+?\s*(?:years?|yrs?\.?)\b", re.IGNORECASE)

# Date-range calculation: CDAC-style resumes give a Work Details table of
# From/To dates per job (mostly DD/MM/YYYY) instead of ever spelling out a
# total. Every date-ish token — a full date, "Month YYYY", a bare year, or
# "Present"/"Current"/"Till date" — is scanned in document order and paired
# up two at a time: (1st, 2nd), (3rd, 4th), ... That naturally covers
# ranges written with "to"/"-"/"–" AND a From/To pair that's simply placed
# next to each other in a table row, since the pairing doesn't depend on
# what (if anything) sits between the two dates at all.
_MONTH_NUM = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_MONTH_NAMES = r"jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"

_FULL_DATE_TOKEN = r"\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}"
_MONTH_YEAR_TOKEN = rf"(?:{_MONTH_NAMES})[a-z]*\.?\s+\d{{4}}"
_YEAR_TOKEN = r"\d{4}"
_PRESENT_WORD = r"present|current(?:ly)?|now|till\s*date|to\s*date"

# Order matters: the most specific shape (full date) must be tried before
# the bare-year alternative, or the year inside a full date would get
# matched on its own instead of as part of the whole date.
_DATE_TOKEN_PATTERN = re.compile(
    rf"{_FULL_DATE_TOKEN}|{_MONTH_YEAR_TOKEN}|{_PRESENT_WORD}|{_YEAR_TOKEN}",
    re.IGNORECASE,
)

_FULL_DATE_RE = re.compile(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})$")
_MONTH_YEAR_RE = re.compile(rf"^({_MONTH_NAMES})[a-z]*\.?\s+(\d{{4}})$", re.IGNORECASE)
_YEAR_ONLY_RE = re.compile(r"^(\d{4})$")
_PRESENT_RE = re.compile(rf"^(?:{_PRESENT_WORD})$", re.IGNORECASE)


def _parse_date_token(token, today):
    """Best-effort parse of one matched token into a datetime.date. Never
    raises — returns None for anything that doesn't parse cleanly, so a
    stray unparseable date is just skipped rather than crashing the
    resume upload."""

    token = token.strip()

    try:
        if _PRESENT_RE.match(token):
            return today

        match = _FULL_DATE_RE.match(token)
        if match:
            first, second, year_str = match.groups()
            year = int(year_str)
            if year < 100:
                year += 2000 if year < 70 else 1900
            first, second = int(first), int(second)
            # These resumes write dates day-first (DD/MM/YYYY); only fall
            # back to month-first if the day-first reading is impossible.
            for day, month in ((first, second), (second, first)):
                try:
                    return datetime.date(year, month, day)
                except ValueError:
                    continue
            return None

        match = _MONTH_YEAR_RE.match(token)
        if match:
            month = _MONTH_NUM.get(match.group(1).lower())
            return datetime.date(int(match.group(2)), month, 1) if month else None

        match = _YEAR_ONLY_RE.match(token)
        if match:
            return datetime.date(int(match.group(1)), 1, 1)
    except (ValueError, TypeError):
        return None

    return None


def _experience_from_date_ranges(text):
    """
    Calculate total work experience from all date ranges found in resume text.
    Works even when PDF tables are extracted as plain text.
    """

    today = datetime.date.today()

    # Match:
    # 08/09/2023 25/07/2025
    # 08/09/2023 - 25/07/2025
    # 08/09/2023 to 25/07/2025
    pattern = re.compile(
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:-|–|to)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|Present|Current|Till Date)",
        re.IGNORECASE,
    )

    total_days = 0

    for start_str, end_str in pattern.findall(text):

        start = _parse_date_token(start_str, today)

        if end_str.lower() in ("present", "current", "till date"):
            end = today
        else:
            end = _parse_date_token(end_str, today)

        if start is None or end is None:
            continue

        if end < start:
            continue

        total_days += (end - start).days

    if total_days == 0:
        return None

    return round(total_days / 365.25)


def _experience_from_tables(tables):
    """Read a Work Details-style table — one with 'From' and 'To' column
    headers, as returned by file_extractor.extract_tables — and sum each
    row's job duration straight from its cells. This is the most reliable
    signal where available: it reads structured cells directly instead of
    reconstructing From/To pairs out of PyMuPDF's linear (row-then-column)
    text dump, which is what breaks once a table has more than one data
    row. Returns None (not 0) if no table has both headers, so the caller
    can tell "no table here" apart from "table found but nothing valid in
    it", and fall back to text-based extraction only for the former."""

    if not tables:
        return None

    today = datetime.date.today()
    max_span_days = 365 * 60  # sanity cap against garbled/misread dates

    total_days = 0
    found_any = False
    for table in tables:
        header_idx = from_idx = to_idx = None
        for r_idx, row in enumerate(table):
            cells = [(cell or "").strip().lower() for cell in row]
            if "from" in cells and "to" in cells:
                header_idx = r_idx
                from_idx = cells.index("from")
                to_idx = cells.index("to")
                break
        if header_idx is None:
            continue  # not a From/To table (e.g. an Academic Details table)

        for row in table[header_idx + 1:]:
            if from_idx >= len(row) or to_idx >= len(row):
                continue
            start = _parse_date_token(row[from_idx], today)
            end = _parse_date_token(row[to_idx], today)
            if start is None or end is None:
                continue
            span_days = (end - start).days
            if span_days <= 0 or span_days > max_span_days:
                continue
            total_days += span_days
            found_any = True

    if not found_any:
        return None
    return round(total_days / 365.25)


def extract_experience(text, tables=None):
    """
    Extract total experience from resume.

    Priority:
    1. Structured tables
    2. Date ranges in text
    3. Explicit 'X years'
    """

    # ---------- TABLES ----------
    if tables:
        years = _experience_from_tables(tables)
        if years is not None:
            return years

    # ---------- DATE RANGES ----------
    years = _experience_from_date_ranges(text)
    if years is not None:
        return years

    # ---------- "3 years" ----------
    matches = EXPERIENCE_PHRASE_PATTERN.findall(text)

    if matches:
        return max(int(x) for x in matches)

    return 0


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
    (src/ai/insights.generate_summary) is preferred when Groq is
    available; this keeps the app useful without it."""

    section = _find_section(text, SECTION_HEADERS["summary"])
    if section:
        return " ".join(section.split())[:400]

    top_skills = ", ".join(skills[:5]) if skills else "no listed skills"
    return f"{experience_years} years of experience. Key skills: {top_skills}."


def parse_resume_text(text, tables=None):
    """Parse raw resume text into a structured candidate dict. `tables`
    (optional) is the structured table data from
    file_extractor.extract_tables, letting extract_experience read a Work
    Details table's From/To columns directly instead of reconstructing
    them from text."""
    skills = extract_skills(text)
    experience_years = extract_experience(text, tables)

    return {
        "name": extract_name(text, tables),
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
    tables = extract_tables(file_bytes, file_path)
    return parse_resume_text(text, tables)


def parse_resume_upload(file_bytes, filename):
    """Parse an in-memory uploaded resume (Streamlit UploadedFile.getvalue()
    bytes + its name). This is the entry point the ATS UI uses."""
    text = extract_text(file_bytes, filename)
    tables = extract_tables(file_bytes, filename)
    result = parse_resume_text(text, tables)
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
