"""Centralised application settings loaded from environment variables / backend/.env."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "NutriPlan API"
    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # No default credentials: the URL must come from the environment.
    database_url: str = Field(
        default="",
        description="SQLAlchemy URL, e.g. postgresql+psycopg://user:pass@host:5433/nutriplan",
    )
    test_database_url: str = ""

    @field_validator("database_url", "test_database_url")
    @classmethod
    def _use_psycopg_driver(cls, url: str) -> str:
        # Hosting providers (e.g. Render, Heroku) hand out postgres:// or postgresql:// URLs;
        # without an explicit driver SQLAlchemy would look for psycopg2, which is not installed.
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url

    # Stored as a comma-separated string so it can be set from a plain env var.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Sessions (OD-12): opaque token in an HttpOnly cookie, hashed in the database.
    session_cookie_name: str = "np_session"
    csrf_cookie_name: str = "np_csrf"
    csrf_header_name: str = "X-CSRF-Token"
    session_ttl_hours: int = Field(default=12, ge=1, le=24 * 30)
    # None → Secure cookies automatically in production, plain HTTP allowed locally.
    cookie_secure: bool | None = None

    # Directory with the built frontend (index.html + assets) to serve in production.
    frontend_dist_dir: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def use_secure_cookies(self) -> bool:
        return self.is_production if self.cookie_secure is None else self.cookie_secure


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance (override in tests via dependency_overrides)."""
    return Settings()
