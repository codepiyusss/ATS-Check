"""
Handles everything related to reading the uploaded PDF resume:
- verifying it is actually a PDF (not just renamed)
- extracting the raw text
- rejecting corrupted / unreadable / empty files

Uses pdfplumber because it has simple, readable text extraction
which is a good fit for a student-level project.
"""

import pdfplumber


class PDFParsingError(Exception):
    """Raised when a PDF can't be read or doesn't contain usable text."""
    pass


def is_valid_pdf(file_path):
    """
    Verify the file actually starts with the PDF magic number (%PDF).
    This is a simple MIME/type check that doesn't just trust the file
    extension - a renamed .exe with a .pdf extension would fail this.
    """
    try:
        with open(file_path, "rb") as f:
            header = f.read(5)
        return header.startswith(b"%PDF-")
    except OSError:
        return False


def extract_text_from_pdf(file_path):
    """
    Extract all text from a PDF file, page by page.
    Raises PDFParsingError if the file is corrupted or has no text
    (e.g. it's a scanned image with no OCR layer).
    """
    if not is_valid_pdf(file_path):
        raise PDFParsingError("The uploaded file is not a valid PDF.")

    extracted_pages = []

    try:
        with pdfplumber.open(file_path) as pdf:
            if len(pdf.pages) == 0:
                raise PDFParsingError("The PDF has no pages.")

            for page in pdf.pages:
                text = page.extract_text() or ""
                extracted_pages.append(text)
    except PDFParsingError:
        raise
    except Exception as exc:
        # pdfplumber raises various low-level exceptions for corrupted
        # or malformed PDFs - we don't want to leak that detail to the
        # user, so we wrap it in our own error type.
        raise PDFParsingError("Could not read the PDF file. It may be corrupted.") from exc

    full_text = "\n".join(extracted_pages).strip()

    if not full_text:
        raise PDFParsingError(
            "No readable text was found in this PDF. "
            "It may be a scanned image without selectable text."
        )

    return full_text
