"""
Small helper/utility functions shared by the routes.

Keeping these separate from routes/pdf_parser/ai_analysis keeps each
file focused on one job, which makes the project easier to follow.
"""

import re
import uuid


def allowed_file(filename, allowed_extensions):
    """Check that the uploaded file has an allowed extension (e.g. pdf)."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def generate_temp_filename(original_filename):
    """
    Build a random, safe filename for temporary storage so we never trust
    the original filename from the user (avoids path traversal issues).
    """
    ext = original_filename.rsplit(".", 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"


def sanitize_text(text, max_length=15000):
    """
    Very basic input sanitization for resume text (pasted or extracted
    from a PDF) before it is sent to the AI model or shown back to the
    user. Removes null bytes/control characters and caps the length so
    someone can't send a huge block of text to the analyzer.
    """
    if not text:
        return ""

    # Strip null bytes and other non-printable control characters
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

    # Collapse excessive blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()[:max_length]


def sanitize_form_field(value, max_length=1000):
    """Basic sanitization for contact form fields (name/email/message)."""
    if not value:
        return ""
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)
    return cleaned.strip()[:max_length]


def score_label(score):
    """Turn a numeric score into a 'Good / Average / Needs Improvement' label."""
    if score >= 75:
        return "Good", "good"
    elif score >= 50:
        return "Average", "average"
    else:
        return "Needs Improvement", "needs-improvement"
