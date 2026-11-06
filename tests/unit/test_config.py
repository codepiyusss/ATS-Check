import pytest

from config import get_config, ProductionConfig


def test_default_is_development(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    assert get_config().__name__ == "DevelopmentConfig"


def test_unknown_env_is_rejected():
    with pytest.raises(RuntimeError):
        get_config("staging-typo")


def test_production_refuses_missing_secret_key(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", None)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        get_config("production")


def test_production_refuses_short_secret_key(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "short")
    with pytest.raises(RuntimeError):
        get_config("production")


def test_production_accepts_strong_key_and_is_not_debug(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "x" * 32)
    cfg = get_config("production")
    assert cfg.DEBUG is False
    assert cfg.SESSION_COOKIE_SECURE is True


def test_testing_config_never_has_gemini_key():
    assert get_config("testing").GEMINI_API_KEY is None
