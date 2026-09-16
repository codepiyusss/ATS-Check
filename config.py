import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    # Only PDF files are accepted.
    ALLOWED_EXTENSIONS = {"pdf"}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
