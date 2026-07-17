import re
import uuid


def allowed_file(filename, allowed_extensions):
    """Check that the uploaded file has an allowed extension (e.g. pdf)."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def generate_temp_filename(original_filename):
    ext = original_filename.rsplit(".", 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"


def sanitize_text(text, max_length=15000):
    if not text:
        return ""

    # Strip null bytes and other non-printable control characters
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

    # Collapse excessive blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()[:max_length]


def sanitize_form_field(value, max_length=1000):
    if not value:
        return ""
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)
    return cleaned.strip()[:max_length]


def score_label(score):
    if score >= 75:
        return "Good", "good"
    elif score >= 50:
        return "Average", "average"
    else:
        return "Needs Improvement", "needs-improvement"
