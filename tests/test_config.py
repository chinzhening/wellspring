import pytest
from pydantic import ValidationError

from core.config import Settings


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://user:pass@localhost:5432/db"
    )

    settings = Settings(_env_file=None) # ignore .env, use monkeypatched vars

    assert settings.database_url == "postgresql://user:pass@localhost:5432/db"


def test_settings_custom_log_level(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://user:pass@localhost:5432/db"
    )
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.log_level == "DEBUG"


def test_settings_optional_keys(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://user:pass@localhost:5432/db"
    )
    monkeypatch.setenv("GEMINI_API_KEY", "abc123")
    monkeypatch.setenv("YOUTUBE_API_KEY", "xyz789")

    settings = Settings()

    assert settings.gemini_api_key == "abc123"
    assert settings.youtube_api_key == "xyz789"


def test_settings_missing_database_url():
    with pytest.raises((ValidationError, RuntimeError)):
        Settings(_env_file=None)
