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


def test_sqlite_database_folder_is_created(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from app.db.session import ensure_sqlite_directory

    target = tmp_path / "new" / "folder" / "nutriplan.db"
    ensure_sqlite_directory(f"sqlite:///{target.as_posix()}")
    assert target.parent.is_dir()
    ensure_sqlite_directory("sqlite://")  # in-memory: nothing to create
    ensure_sqlite_directory("postgresql+psycopg://u:p@localhost/db")  # not SQLite: no-op


@pytest.mark.parametrize(
    "given",
    ["postgres://u:p@db.example.com:5432/app", "postgresql://u:p@db.example.com:5432/app"],
)
def test_hosted_database_urls_use_the_psycopg_driver(given: str) -> None:
    settings = Settings(_env_file=None, database_url=given, test_database_url=given)
    assert settings.database_url == "postgresql+psycopg://u:p@db.example.com:5432/app"
    assert settings.test_database_url == settings.database_url
    sqlite = Settings(_env_file=None, database_url="sqlite:///x.db")
    assert sqlite.database_url == "sqlite:///x.db"
