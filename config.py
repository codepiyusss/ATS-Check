import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # Secret key is used by Flask for sessions/flash messages.
    # In production this MUST be set as an environment variable.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # Where uploaded resumes are temporarily stored before/while parsing.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    # Only PDF files are accepted.
    ALLOWED_EXTENSIONS = {"pdf"}

    # 5 MB max upload size (matches the "Maximum file size: 5 MB" note on the page)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # API key for the AI provider (Gemini). If this is not set, the app
    # falls back to a simple built-in heuristic analyzer so the project
    # still works out of the box during development/demos.
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
