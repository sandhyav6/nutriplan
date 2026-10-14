"""REQ-4.1.1, REQ-4.1.2, SRS §5.3 – registration, login, logout, sessions, CSRF, RBAC."""

from sqlalchemy import select

from app.models import User, UserSession
from app.models.enums import UserRole


def test_register_creates_user_session_and_never_admin(api, db) -> None:  # type: ignore[no-untyped-def]
    response = api.register()
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["user"]["email"] == "asha@example.com"
    assert body["user"]["role"] == "user"
    assert body["has_profile"] is False
    user = db.scalar(select(User))
    assert user.role == UserRole.USER
    assert user.password_hash != "Secret123" and user.password_hash.startswith("$argon2id$")
    # Only the hash of the session token is stored.
    session = db.scalar(select(UserSession))
    assert len(session.token_hash) == 64
    assert api.client.cookies.get("np_session") != session.token_hash
    assert api.get("/auth/me").json()["user"]["email"] == "asha@example.com"


def test_session_cookie_is_httponly(api) -> None:  # type: ignore[no-untyped-def]
    response = api.register()
    cookies = response.headers.get_list("set-cookie")
    session_cookie = next(c for c in cookies if c.startswith("np_session="))
    assert "HttpOnly" in session_cookie
    assert "samesite=lax" in session_cookie.lower()
    csrf_cookie = next(c for c in cookies if c.startswith("np_csrf="))
    assert "HttpOnly" not in csrf_cookie


def test_register_rejects_role_field(api) -> None:  # type: ignore[no-untyped-def]
    response = api.post(
        "/auth/register",
        {"full_name": "Eve", "email": "eve@example.com", "password": "Secret123", "role": "admin"},
    )
    assert response.status_code == 422


def test_register_duplicate_email_case_insensitive(api) -> None:  # type: ignore[no-untyped-def]
    assert api.register().status_code == 201
    response = api.register(email="ASHA@Example.com")
    assert response.status_code == 409
    assert response.json()["error"]["details"]["field"] == "email"


def test_register_validates_password_and_email(api) -> None:  # type: ignore[no-untyped-def]
    assert api.register(password="short1").status_code == 422
    response = api.register(password="allletters")
    assert response.status_code == 422
    assert "letter and one number" in str(response.json())
    assert api.register(email="not-an-email").status_code == 422


def test_login_success_and_failure(make_api) -> None:  # type: ignore[no-untyped-def]
    make_api().register()
    other = make_api()
    bad = other.post("/auth/login", {"email": "asha@example.com", "password": "Wrong123"})
    assert bad.status_code == 401
    assert bad.json()["error"]["message"] == "Invalid email or password."
    unknown = other.post("/auth/login", {"email": "nobody@example.com", "password": "Wrong123"})
    assert unknown.status_code == 401
    ok = other.post("/auth/login", {"email": "Asha@example.com", "password": "Secret123"})
    assert ok.status_code == 200
    assert other.get("/auth/me").status_code == 200


def test_logout_revokes_session(api, db) -> None:  # type: ignore[no-untyped-def]
    api.register()
    token = api.client.cookies.get("np_session")
    assert api.post("/auth/logout").status_code == 204
    assert db.scalar(select(UserSession)) is None
    api.client.cookies.set("np_session", token)  # replaying the old cookie must not work
    assert api.get("/auth/me").status_code == 401


def test_private_endpoints_require_login(api) -> None:  # type: ignore[no-untyped-def]
    for path in (
        "/auth/me",
        "/profile",
        "/meal-plans/current",
        "/grocery-lists/current",
        "/dashboard",
    ):
        response = api.get(path)
        assert response.status_code == 401, path
        assert response.json()["error"]["code"] == "unauthorized"


def test_state_changing_requests_need_csrf_token(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Asha", "email": "a@example.com", "password": "Secret123"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_failed"
    client.get("/api/v1/auth/csrf")
    wrong = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Asha", "email": "a@example.com", "password": "Secret123"},
        headers={"X-CSRF-Token": "forged"},
    )
    assert wrong.status_code == 403


def test_admin_routes_enforce_role(api, admin_api) -> None:  # type: ignore[no-untyped-def]
    assert api.get("/admin/foods").status_code == 401
    api.register()
    forbidden = api.get("/admin/foods")
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["message"] == "Administrator access is required."
    assert admin_api.get("/admin/foods").status_code == 200
    assert admin_api.get("/auth/me").json()["user"]["role"] == "admin"


def test_cli_create_admin_reads_environment(session_factory, monkeypatch, db) -> None:  # type: ignore[no-untyped-def]
    from app import cli

    monkeypatch.setattr(cli, "get_session_factory", lambda: session_factory)
    monkeypatch.delenv("NUTRIPLAN_ADMIN_EMAIL", raising=False)
    assert cli.main(["create-admin"]) == 2
    monkeypatch.setenv("NUTRIPLAN_ADMIN_EMAIL", "Boss@Example.com")
    monkeypatch.setenv("NUTRIPLAN_ADMIN_PASSWORD", "weak")
    assert cli.main(["create-admin"]) == 2
    monkeypatch.setenv("NUTRIPLAN_ADMIN_PASSWORD", "BossPass123")
    assert cli.main(["create-admin"]) == 0
    db.expire_all()
    admin = db.scalar(select(User).where(User.email == "boss@example.com"))
    assert admin is not None and admin.role == UserRole.ADMIN
    assert cli.main(["create-admin"]) == 0  # idempotent: promotes / updates
