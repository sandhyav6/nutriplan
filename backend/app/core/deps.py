"""Request dependencies: database session and authentication / authorisation (SRS §5.3)."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_token
from app.db.session import get_db
from app.models import User
from app.models.enums import UserRole
from app.repositories import users as user_repo

DbSession = Annotated[Session, Depends(get_db)]


def get_optional_user(request: Request, db: DbSession) -> User | None:
    token = request.cookies.get(get_settings().session_cookie_name)
    if not token:
        return None
    user = user_repo.get_user_for_session(db, hash_token(token))
    if user is None or not user.is_active:
        return None
    return user


def require_user(user: Annotated[User | None, Depends(get_optional_user)]) -> User:
    """Authentication is required for all private data."""
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please log in to continue.")
    return user


def require_admin(user: Annotated[User, Depends(require_user)]) -> User:
    """Administrator role is required (REQ-4.7.1). Enforced on the backend, not only in the UI."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator access is required.")
    return user


CurrentUser = Annotated[User, Depends(require_user)]
AdminUser = Annotated[User, Depends(require_admin)]
