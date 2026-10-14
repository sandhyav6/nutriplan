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


def test_method_not_allowed_uses_consistent_error_shape(api) -> None:  # type: ignore[no-untyped-def]
    response = api.post("/health")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_request_id_header_is_returned(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "abc123"})
    assert response.headers["X-Request-ID"] == "abc123"


def test_serves_built_frontend_when_configured(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from app.core.config import get_settings
    from app.main import create_app

    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text('<div id="root"></div>', encoding="utf-8")
    (tmp_path / "assets" / "app.js").write_text("export {}", encoding="utf-8")
    (tmp_path / "favicon.svg").write_text("<svg/>", encoding="utf-8")
    monkeypatch.setenv("FRONTEND_DIST_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as spa:
            assert 'id="root"' in spa.get("/").text
            assert 'id="root"' in spa.get("/meal-plan/meals/3").text  # client-side route
            assert spa.get("/assets/app.js").text == "export {}"
            assert spa.get("/favicon.svg").text == "<svg/>"
            missing_api = spa.get("/api/v1/does-not-exist")
            assert missing_api.status_code == 404
            assert missing_api.json()["error"]["code"] == "not_found"
            assert spa.get("/docs").status_code == 200
    finally:
        monkeypatch.delenv("FRONTEND_DIST_DIR")
        get_settings.cache_clear()
