"""PostgreSQL integration tests – run only when TEST_DATABASE_URL points to a test database."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.models import Base

BACKEND_DIR = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.integration


def _alembic_config(url: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.cmd_opts = type("Opts", (), {"x": [f"db_url={url}"]})()  # type: ignore[assignment]
    return cfg


def test_migrations_upgrade_and_downgrade(test_database_url: str) -> None:
    cfg = _alembic_config(test_database_url)
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")

    engine = create_engine(test_database_url)
    try:
        tables = set(inspect(engine).get_table_names())
        assert set(Base.metadata.tables) <= tables
        with engine.connect() as connection:
            slots = connection.execute(
                text("SELECT slot FROM meal_categories ORDER BY display_order")
            )
            assert [row[0] for row in slots] == ["breakfast", "lunch", "dinner", "snack"]
            allergen_count = connection.execute(text("SELECT COUNT(*) FROM allergens")).scalar_one()
            assert allergen_count == 10
    finally:
        engine.dispose()

    command.downgrade(cfg, "base")
    engine = create_engine(test_database_url)
    try:
        assert "users" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()
    command.upgrade(cfg, "head")


def test_database_rejects_invalid_enum_value(test_database_url: str) -> None:
    command.upgrade(_alembic_config(test_database_url), "head")
    engine = create_engine(test_database_url)
    try:
        with engine.connect() as connection, pytest.raises(Exception, match="check"):
            connection.execute(
                text(
                    "INSERT INTO users (email, full_name, password_hash, role) "
                    "VALUES ('x@example.test', 'X', 'hash', 'superuser')"
                )
            )
    finally:
        engine.dispose()
