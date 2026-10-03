"""Tests for extract_name()'s table-aware fix in src/parser/resume_parser.py.

Covers the exact anomaly reported: a resume whose top-of-page content is a
table (Personal Details / Candidate Details grid) previously extracted the
table's own header row ("Name Email Phone Address") as the candidate's
name, because that flattened line passes the same "2-4 alphabetic words"
heuristic a real name would pass.
"""

from src.parser.resume_parser import extract_name, parse_resume_text


def test_plain_text_resume_name_unaffected():
    """The common case (name as the first line) must keep working exactly
    as before — this is a no-regression check."""
    text = "Rahul Verma\nData Analyst\nrahul.verma@example.com\n+91 9812345678"
    assert extract_name(text) == "Rahul Verma"


def test_label_value_row_table():
    """Layout 1: ['Name', 'John Doe'] in the same row."""
    tables = [[
        ["Name", "John Doe"],
        ["Email", "john.doe@example.com"],
        ["Phone", "9876543210"],
    ]]
    # Deliberately garbled/irrelevant top-of-text, like a flattened table
    # dump would produce, to prove the table path is what's used.
    text = "Name Email Phone John Doe john.doe@example.com 9876543210"
    assert extract_name(text, tables) == "John Doe"


def test_header_then_data_row_table():
    """Layout 2: header row ['Name', 'Email', 'Phone'] then a data row
    directly below it, the same shape as the existing Work Details
    From/To table reading."""
    tables = [[
        ["Name", "Email", "Phone"],
        ["Priya Sharma", "priya@example.com", "9123456780"],
    ]]
    text = "Name Email Phone Priya Sharma priya@example.com 9123456780"
    assert extract_name(text, tables) == "Priya Sharma"


def test_flattened_table_header_not_mistaken_for_name_without_table_data():
    """Even without structured tables available, a bare label row like
    'Name Email Phone Address' must not be returned as a name — it should
    fall through to 'Unknown' rather than reporting a header as a person."""
    text = "Name Email Phone Address\n(no other identifiable line here)"
    assert extract_name(text) == "Unknown"


def test_table_takes_priority_over_misleading_text():
    """When both a table and confusing top-of-text are present, the
    structured table wins — this is the actual bug scenario end-to-end
    through parse_resume_text."""
    tables = [[
        ["Candidate Name", "Ananya Iyer"],
        ["Email", "ananya.iyer@example.com"],
    ]]
    text = "Personal Details\nName Email Phone\nAnanya Iyer ananya.iyer@example.com"
    result = parse_resume_text(text, tables)
    assert result["name"] == "Ananya Iyer"


def test_no_table_falls_back_to_text_heuristic():
    """tables=None (e.g. a .txt upload, which has no table concept) must
    still work via the original line-scanning heuristic."""
    text = "Karan Mehta\nMarketing Analyst\nkaran.mehta@example.com"
    assert extract_name(text, tables=None) == "Karan Mehta"


def test_unrelated_table_does_not_interfere():
    """A table with no name-labeled cell (e.g. a Work Details/From-To
    table) must not accidentally supply a wrong 'name' — extraction
    should fall through to the text heuristic."""
    tables = [[
        ["From", "To", "Company"],
        ["01/01/2020", "01/01/2022", "Acme Corp"],
    ]]
    text = "Rahul Verma\nSenior Analyst"
    assert extract_name(text, tables) == "Rahul Verma"
