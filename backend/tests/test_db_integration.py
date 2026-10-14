"""PostgreSQL integration tests – run only when TEST_DATABASE_URL points to a test database."""

from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import build_engine, get_db
from app.main import create_app
from app.models import Base
from app.services.seed_service import seed_catalogue
from tests.conftest import VALID_PROFILE, ApiClient

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


def test_full_user_flow_on_postgresql(test_database_url: str) -> None:
    """Seed → register → profile → plan → feedback → replace → grocery → dashboard on PostgreSQL."""
    cfg = _alembic_config(test_database_url)
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    engine = build_engine(test_database_url)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    try:
        with factory() as db:
            assert seed_catalogue(db)["recipes"] > 0

        application = create_app()

        def _db() -> Iterator[Session]:
            with factory() as session:
                yield session

        application.dependency_overrides[get_db] = _db
        with TestClient(application) as client:
            api = ApiClient(client)
            assert api.register().status_code == 201
            assert api.put("/profile", VALID_PROFILE).status_code == 201

            response = api.post("/meal-plans/generate")
            assert response.status_code == 201, response.text
            plan = response.json()
            assert len(plan["meals"]) == 28
            assert Decimal(plan["total_cost_inr"]) <= Decimal(VALID_PROFILE["weekly_budget_inr"])
            filled = [m for m in plan["meals"] if m["meal"]]
            assert filled

            feedback = api.post(
                "/feedback", {"planned_meal_id": filled[0]["id"], "feedback_type": "favourite"}
            )
            assert feedback.status_code == 201, feedback.text
            before = api.get("/grocery-lists/current").json()
            replaced = api.post(f"/meal-plans/current/meals/{filled[1]['id']}/replace")
            assert replaced.status_code in (200, 409), replaced.text
            after = api.get("/grocery-lists/current")
            assert after.status_code == 200
            if replaced.status_code == 200:
                assert after.json()["generated_at"] >= before["generated_at"]

            dash = api.get("/dashboard").json()
            assert dash["has_plan"] is True
            assert [f["recipe_id"] for f in dash["favourites"]] == [filled[0]["meal"]["recipe_id"]]
    finally:
        engine.dispose()
        command.downgrade(cfg, "base")
        command.upgrade(cfg, "head")
