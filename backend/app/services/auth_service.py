"""Registration, login, logout and admin bootstrap (UC-01 – UC-03, REQ-4.1.1, REQ-4.1.2)."""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.csrf import set_csrf_cookie
from app.core.security import (
    generate_token,
    hash_password,
    hash_token,
    password_needs_rehash,
    verify_password,
)
from app.models import User
from app.models.enums import UserRole
from app.repositories import users as user_repo
from app.schemas.auth import LoginRequest, RegisterRequest


def register(db: Session, data: RegisterRequest) -> User:
    if user_repo.get_by_email(db, data.email):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"field": "email", "message": "An account with this email already exists."},
        )
    # Public registration always creates a normal user – the role is never client-controlled.
    user = user_repo.create_user(
        db, email=data.email, full_name=data.full_name, password_hash=hash_password(data.password)
    )
    db.commit()
    return user


def authenticate(db: Session, data: LoginRequest) -> User:
    user = user_repo.get_by_email(db, data.email)
    valid = verify_password(data.password, user.password_hash if user else None)
    if user is None or not valid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated.")
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(data.password)
        db.commit()
    return user


def start_session(db: Session, user: User, response: Response) -> None:
    """Create a server-side session and set the session + fresh CSRF cookies."""
    settings = get_settings()
    token = generate_token()
    expires_at = datetime.now(UTC) + timedelta(hours=settings.session_ttl_hours)
    user_repo.delete_expired_sessions(db, user.id)
    user_repo.create_session(
        db, user_id=user.id, token_hash=hash_token(token), expires_at=expires_at
    )
    db.commit()
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.use_secure_cookies,
        samesite="lax",
        path="/",
    )
    set_csrf_cookie(response, generate_token())  # rotate CSRF token on login


def end_session(db: Session, session_token: str | None, response: Response) -> None:
    settings = get_settings()
    if session_token:
        user_repo.delete_session(db, hash_token(session_token))
        db.commit()
    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        httponly=True,
        secure=settings.use_secure_cookies,
        samesite="lax",
    )


def create_or_promote_admin(db: Session, *, email: str, full_name: str, password: str) -> str:
    """Admin bootstrap used by the CLI. Returns 'created' or 'promoted'."""
    RegisterRequest(full_name=full_name, email=email, password=password)  # same rules as users
    user = user_repo.get_by_email(db, email)
    if user is None:
        user_repo.create_user(
            db,
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
        )
        result = "created"
    else:
        user.role = UserRole.ADMIN
        user.password_hash = hash_password(password)
        user.is_active = True
        result = "promoted"
    db.commit()
    return result
