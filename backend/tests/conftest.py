"""Shared pytest fixtures."""

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "test")

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL") or get_settings().test_database_url
    if not url:
        pytest.skip("TEST_DATABASE_URL is not configured – skipping PostgreSQL integration test.")
    return url
