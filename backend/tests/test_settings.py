import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_load_from_explicit_values() -> None:
    settings = Settings(
        _env_file=None,
        environment="test",
        database_url="postgresql+psycopg://u:p@localhost:5433/db",
        cors_origins="http://localhost:5173, http://example.test ,",
    )
    assert settings.environment == "test"
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.cors_origin_list == ["http://localhost:5173", "http://example.test"]
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.is_production is False


def test_settings_read_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "NutriPlan Test")
    monkeypatch.setenv("ENVIRONMENT", "production")
    settings = Settings(_env_file=None)
    assert settings.app_name == "NutriPlan Test"
    assert settings.is_production is True


def test_settings_reject_unknown_environment() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="staging")  # type: ignore[arg-type]
