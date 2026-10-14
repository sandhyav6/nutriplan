"""Profile and reference-data persistence."""

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Allergen, Food, UserProfile


def get_for_user(db: Session, user_id: int) -> UserProfile | None:
    return db.scalar(
        select(UserProfile)
        .where(UserProfile.user_id == user_id)
        .options(selectinload(UserProfile.allergens), selectinload(UserProfile.excluded_foods))
    )


def list_allergens(db: Session) -> list[Allergen]:
    return list(db.scalars(select(Allergen).order_by(Allergen.name)))


def get_allergens(db: Session, ids: Iterable[int]) -> list[Allergen]:
    ids = list(ids)
    if not ids:
        return []
    return list(db.scalars(select(Allergen).where(Allergen.id.in_(ids))))


def get_foods(db: Session, ids: Iterable[int]) -> list[Food]:
    ids = list(ids)
    if not ids:
        return []
    return list(db.scalars(select(Food).where(Food.id.in_(ids))))
