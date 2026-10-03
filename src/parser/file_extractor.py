"""
Unified text extraction for uploaded files.

Consolidates what used to be a PDF-only script (src/parser/pdf_extractor.py)
into one entry point that handles the three formats the spec requires for
both resumes and job descriptions: PDF, DOCX, TXT. Resume parsing and JD
parsing both call `extract_text`, so the format-handling logic lives in
exactly one place.
"""

import io
import os

SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".txt")


def _extract_pdf_text(file_bytes):
    import fitz  # PyMuPDF

    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
        for page in pdf:
            text += page.get_text()
    return text


def _extract_pdf_tables(file_bytes):
    """Detect tables via PyMuPDF's find_tables() and return each as a list
    of rows (list of cell strings), preserving row/column structure.

    Plain page.get_text() reads a table's cells in visual reading order —
    header row first, then each data row — which separates a column's
    label (e.g. 'From') from its value and loses which cells belong to
    which row once there's more than one. find_tables() keeps that
    structure intact instead of requiring it to be reconstructed from
    linear text.
    """
    import fitz  # PyMuPDF

    tables = []
    with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
        for page in pdf:
            try:
                found = page.find_tables()
            except Exception:
                continue
            for table in found.tables:
                try:
                    rows = table.extract()
                except Exception:
                    continue
                clean_rows = [
                    ["" if cell is None else str(cell).strip() for cell in row]
                    for row in rows
                ]
                if clean_rows:
                    tables.append(clean_rows)
    return tables


def _extract_docx_text(file_bytes):
    import docx

    document = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in document.paragraphs]

    # Tables (skills/experience are sometimes laid out in a table).
    for table in document.tables:
        for row in table.rows:
            paragraphs.append(" ".join(cell.text for cell in row.cells))

    return "\n".join(paragraphs)


def _extract_docx_tables(file_bytes):
    """Same structured (rows-of-cells) form as _extract_pdf_tables, for
    DOCX's own native table objects."""
    import docx

    document = docx.Document(io.BytesIO(file_bytes))
    tables = []
    for table in document.tables:
        rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        if rows:
            tables.append(rows)
    return tables


def _extract_txt_text(file_bytes):
    return file_bytes.decode("utf-8", errors="ignore")


def extract_text(file_bytes, filename):
    """Extract raw text from an uploaded file's bytes based on its extension.

    Raises ValueError for unsupported formats so callers can surface a
    clear message instead of a stack trace.
    """

    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return _extract_pdf_text(file_bytes)
    if ext == ".docx":
        return _extract_docx_text(file_bytes)
    if ext == ".txt":
        return _extract_txt_text(file_bytes)

    raise ValueError(
        f"Unsupported file type '{ext}' for '{filename}'. "
        f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
    )


def extract_tables(file_bytes, filename):
    """Extract any tables in the file as a list of tables, each table a
    list of rows, each row a list of cell strings — column structure
    preserved, unlike extract_text()'s linear reading-order dump. Returns
    [] for formats/files with no detected tables (including .txt, which
    has no table concept) rather than raising, since callers should treat
    "no tables" as a normal case to fall back from.
    """

    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return _extract_pdf_tables(file_bytes)
    if ext == ".docx":
        return _extract_docx_tables(file_bytes)
    return []


def is_supported(filename):
    return os.path.splitext(filename)[1].lower() in SUPPORTED_EXTENSIONS
