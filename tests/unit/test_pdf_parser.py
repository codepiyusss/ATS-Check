import pytest

from tests.fixtures.pdf_factory import make_pdf, RESUME_LINES
from utils.pdf_parser import extract_text_from_pdf, PDFParsingError


def _write(tmp_path, data, name="f.pdf"):
    p = tmp_path / name
    p.write_bytes(data)
    return str(p)


def test_valid_pdf_text_is_extracted(tmp_path):
    text = extract_text_from_pdf(_write(tmp_path, make_pdf(RESUME_LINES)))
    assert "Python developer" in text and "jane@example.com" in text


def test_non_pdf_content_is_rejected(tmp_path):
    with pytest.raises(PDFParsingError, match="not a valid PDF"):
        extract_text_from_pdf(_write(tmp_path, b"MZ\x90 this is an exe"))


def test_empty_file_is_rejected(tmp_path):
    with pytest.raises(PDFParsingError):
        extract_text_from_pdf(_write(tmp_path, b""))


def test_corrupted_pdf_gives_friendly_error(tmp_path):
    data = make_pdf(RESUME_LINES)[:60]  # valid header, truncated body
    with pytest.raises(PDFParsingError):
        extract_text_from_pdf(_write(tmp_path, data))


def test_pdf_without_text_is_reported(tmp_path):
    with pytest.raises(PDFParsingError, match="No readable text"):
        extract_text_from_pdf(_write(tmp_path, make_pdf([])))
