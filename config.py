"""Application configuration.

Three environments, chosen by the APP_ENV variable:
    development (default) - local work, debug helpers allowed
    production            - refuses to start without a real SECRET_KEY
    testing               - used by pytest, never touches real services
"""
import os
import tempfile

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_EXTENSIONS = {"pdf"}

    # Kept for now so behaviour is unchanged. Removed in Phases 3-4.
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False

    # Set TRUST_PROXY=1 ONLY when deployed behind Render (see docs/DEPLOYMENT.md).
    TRUST_PROXY = os.environ.get("TRUST_PROXY") == "1"

    RATE_LIMIT_WINDOW = 60  # seconds
    RATE_LIMIT_MAX_REQUESTS = 5


class DevelopmentConfig(Config):
    DEBUG = True
    # A fixed key is acceptable ONLY for local development.
    SECRET_KEY = Config.SECRET_KEY or "dev-only-insecure-key"


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def validate(cls):
        if not cls.SECRET_KEY or len(cls.SECRET_KEY) < 16:
            raise RuntimeError(
                "SECRET_KEY must be set to a random value of at least 16 "
                "characters when APP_ENV=production."
            )


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    GEMINI_API_KEY = None  # tests must never call an external service
    TRUST_PROXY = False
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), "ats_check_test_uploads")


_CONFIGS = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(name=None):
    """Return the config class for `name` (or APP_ENV, default 'development')."""
    env = (name or os.environ.get("APP_ENV") or "development").lower()
    if env not in _CONFIGS:
        raise RuntimeError(
            f"Unknown APP_ENV '{env}'. Use one of: {', '.join(_CONFIGS)}."
        )
    cfg = _CONFIGS[env]
    if hasattr(cfg, "validate"):
        cfg.validate()
    return cfg
