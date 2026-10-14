"""User and session persistence."""

from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import User, UserSession
from app.models.enums import UserRole


def normalise_email(email: str) -> str:
    return email.strip().lower()


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == normalise_email(email)))


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_user(
    db: Session, *, email: str, full_name: str, password_hash: str, role: UserRole = UserRole.USER
) -> User:
    user = User(
        email=normalise_email(email),
        full_name=full_name.strip(),
        password_hash=password_hash,
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def create_session(db: Session, *, user_id: int, token_hash: str, expires_at: datetime) -> None:
    db.add(UserSession(user_id=user_id, token_hash=token_hash, expires_at=expires_at))
    db.flush()


def _as_utc(value: datetime) -> datetime:
    # SQLite (tests) returns naive datetimes; PostgreSQL returns aware ones.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def get_user_for_session(db: Session, token_hash: str) -> User | None:
    session = db.scalar(select(UserSession).where(UserSession.token_hash == token_hash))
    if session is None:
        return None
    if _as_utc(session.expires_at) <= datetime.now(UTC):
        db.delete(session)
        db.commit()
        return None
    return session.user


def delete_session(db: Session, token_hash: str) -> None:
    db.execute(delete(UserSession).where(UserSession.token_hash == token_hash))


def delete_expired_sessions(db: Session, user_id: int) -> None:
    db.execute(
        delete(UserSession).where(
            UserSession.user_id == user_id, UserSession.expires_at <= datetime.now(UTC)
        )
    )
