from fastapi.testclient import TestClient


def test_app_imports() -> None:
    from app.main import app

    assert app.title


def test_openapi_lists_versioned_health_route(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/health" in paths


def test_swagger_docs_available(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_unknown_route_uses_consistent_error_shape(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Not Found"}}


def test_method_not_allowed_uses_consistent_error_shape(client: TestClient) -> None:
    response = client.post("/api/v1/health")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_request_id_header_is_returned(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "abc123"})
    assert response.headers["X-Request-ID"] == "abc123"
