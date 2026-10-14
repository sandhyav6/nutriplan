"""Read-only reference data used by forms (allergens, foods, categories)."""

from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.models import Food, MealCategory
from app.repositories import profiles as profile_repo
from app.schemas.profile import NamedRef

router = APIRouter(tags=["reference"])


@router.get("/allergens", response_model=list[NamedRef])
def list_allergens(db: DbSession) -> list[NamedRef]:
    return [NamedRef.model_validate(a) for a in profile_repo.list_allergens(db)]


@router.get("/foods", response_model=list[NamedRef])
def list_foods(_: CurrentUser, db: DbSession) -> list[NamedRef]:
    """Food names for the 'foods I can't eat' picker on the profile form."""
    return [NamedRef.model_validate(f) for f in db.scalars(select(Food).order_by(Food.name))]


@router.get("/meal-categories", response_model=list[NamedRef])
def list_categories(db: DbSession) -> list[NamedRef]:
    rows = db.scalars(select(MealCategory).order_by(MealCategory.display_order))
    return [NamedRef.model_validate(c) for c in rows]
