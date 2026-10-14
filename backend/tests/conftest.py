"""Shared pytest fixtures.

API tests run against an in-memory SQLite database (schema from the models, reference data
inserted like the initial migration). PostgreSQL-specific checks live in
``test_db_integration.py`` and run when TEST_DATABASE_URL is set (always in CI).
"""

import os
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import insert
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("ENVIRONMENT", "test")

from app.core.config import get_settings
from app.db.session import build_engine, get_db
from app.main import create_app
from app.models import Allergen, Base, MealCategory
from app.models.enums import MealSlot

ALLERGENS = [
    "Peanuts",
    "Tree Nuts",
    "Dairy",
    "Egg",
    "Gluten",
    "Soy",
    "Fish",
    "Shellfish",
    "Sesame",
    "Mustard",
]


def _seed_reference(db: Session) -> None:
    db.execute(
        insert(MealCategory),
        [
            {"slot": MealSlot.BREAKFAST, "name": "Breakfast", "display_order": 1},
            {"slot": MealSlot.LUNCH, "name": "Lunch", "display_order": 2},
            {"slot": MealSlot.DINNER, "name": "Dinner", "display_order": 3},
            {"slot": MealSlot.SNACK, "name": "Snack", "display_order": 4},
        ],
    )
    db.execute(insert(Allergen), [{"name": n} for n in ALLERGENS])
    db.commit()


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = build_engine("sqlite://")
    engine.pool = StaticPool(engine.pool._creator)  # one shared in-memory connection
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as db:
        _seed_reference(db)
    yield factory
    engine.dispose()


@pytest.fixture
def db(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_factory() as session:
        yield session


class ApiClient:
    """TestClient wrapper that sends the CSRF header on state-changing requests."""

    def __init__(self, client: TestClient) -> None:
        self.client = client
        self.client.get("/api/v1/auth/csrf")

    def _headers(self) -> dict[str, str]:
        settings = get_settings()
        token = self.client.cookies.get(settings.csrf_cookie_name)
        return {settings.csrf_header_name: token} if token else {}

    def get(self, path: str, **kw: Any):  # type: ignore[no-untyped-def]
        return self.client.get(f"/api/v1{path}", **kw)

    def post(self, path: str, json: Any = None, **kw: Any):  # type: ignore[no-untyped-def]
        return self.client.post(f"/api/v1{path}", json=json, headers=self._headers(), **kw)

    def put(self, path: str, json: Any = None, **kw: Any):  # type: ignore[no-untyped-def]
        return self.client.put(f"/api/v1{path}", json=json, headers=self._headers(), **kw)

    def delete(self, path: str, **kw: Any):  # type: ignore[no-untyped-def]
        return self.client.delete(f"/api/v1{path}", headers=self._headers(), **kw)

    def register(
        self, email: str = "asha@example.com", password: str = "Secret123", name: str = "Asha"
    ):  # type: ignore[no-untyped-def]
        return self.post(
            "/auth/register", {"full_name": name, "email": email, "password": password}
        )


@pytest.fixture
def app(session_factory: sessionmaker[Session]):  # type: ignore[no-untyped-def]
    application = create_app()

    def _db() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    application.dependency_overrides[get_db] = _db
    return application


@pytest.fixture
def client(app) -> Iterator[TestClient]:  # type: ignore[no-untyped-def]
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api(client: TestClient) -> ApiClient:
    return ApiClient(client)


@pytest.fixture
def make_api(app):  # type: ignore[no-untyped-def]
    """Factory for additional independent browser sessions."""
    clients: list[TestClient] = []

    def _make() -> ApiClient:
        c = TestClient(app)
        clients.append(c)
        return ApiClient(c)

    yield _make
    for c in clients:
        c.close()


@pytest.fixture
def seeded(db: Session) -> Session:
    from app.services.seed_service import seed_catalogue

    seed_catalogue(db)
    return db


@pytest.fixture
def admin_api(make_api, db: Session) -> ApiClient:  # type: ignore[no-untyped-def]
    from app.services.auth_service import create_or_promote_admin

    create_or_promote_admin(db, email="admin@example.com", full_name="Admin", password="AdminPass1")
    admin = make_api()
    response = admin.post("/auth/login", {"email": "admin@example.com", "password": "AdminPass1"})
    assert response.status_code == 200, response.text
    return admin


VALID_PROFILE = {
    "age": 21,
    "gender": "female",
    "height_cm": "160",
    "weight_kg": "55",
    "activity_level": "moderately_active",
    "dietary_preference": "vegetarian",
    "health_goal": "maintenance",
    "weekly_budget_inr": "1500",
    "max_cooking_time_min": 30,
    "allergen_ids": [],
    "excluded_food_ids": [],
}


@pytest.fixture
def test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL") or get_settings().test_database_url
    if not url:
        pytest.skip("TEST_DATABASE_URL is not configured – skipping PostgreSQL integration test.")
    return url
