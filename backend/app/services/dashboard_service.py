"""Dashboard summary (UC-12, REQ-4.6.1 – REQ-4.6.4)."""

from collections import Counter
from dataclasses import asdict
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Feedback, GroceryList, Recipe, User
from app.repositories import profiles as profile_repo
from app.rule_engine import config
from app.schemas.plan import DashboardOut, FavouriteOut
from app.schemas.profile import NutritionTargetOut
from app.services import feedback_service, meal_plan_service
from app.services.profile_service import nutrition_for

ZERO = Decimal("0")


def summary(db: Session, user: User) -> DashboardOut:
    profile = profile_repo.get_for_user(db, user.id)
    favourite_ids = feedback_service.favourite_recipe_ids(db, user.id)
    favourites = (
        [
            FavouriteOut(recipe_id=r.id, name=r.name, slot=r.category.slot)
            for r in db.scalars(
                select(Recipe)
                .where(Recipe.id.in_(favourite_ids))
                .options(selectinload(Recipe.category))
                .order_by(Recipe.name)
            )
        ]
        if favourite_ids
        else []
    )
    total_events = (
        db.scalar(select(func.count()).select_from(Feedback).where(Feedback.user_id == user.id))
        or 0
    )

    plan = meal_plan_service.get_active_plan(db, user) if profile else None
    base = {
        "nutrition": NutritionTargetOut(**asdict(nutrition_for(profile))) if profile else None,
        "weekly_budget_inr": profile.weekly_budget_inr if profile else None,
        "favourites": favourites,
        "total_feedback_events": total_events,
    }
    if plan is None:
        return DashboardOut(
            has_plan=False,
            week_start_date=None,
            total_calories_kcal=ZERO,
            average_daily_calories_kcal=ZERO,
            average_daily_protein_g=ZERO,
            estimated_spend_inr=ZERO,
            days=[],
            meals_by_slot={},
            unavailable_slots=0,
            feedback_on_plan={},
            **base,
        )

    out = meal_plan_service.plan_out(db, user, plan)
    filled = [m for m in out.meals if m.meal]
    grocery = db.scalar(select(GroceryList).where(GroceryList.meal_plan_id == plan.id))
    states = Counter(m.feedback.value if m.feedback else "none" for m in filled)
    days = config.DAYS_PER_PLAN
    total_calories = sum((m.meal.calories_kcal for m in filled), ZERO)  # type: ignore[union-attr]
    total_protein = sum((m.meal.protein_g for m in filled), ZERO)  # type: ignore[union-attr]
    return DashboardOut(
        has_plan=True,
        week_start_date=plan.week_start_date,
        total_calories_kcal=total_calories,
        average_daily_calories_kcal=(total_calories / days).quantize(Decimal("1")),
        average_daily_protein_g=(total_protein / days).quantize(Decimal("0.1")),
        estimated_spend_inr=grocery.total_estimated_cost_inr if grocery else out.total_cost_inr,
        days=out.days,
        meals_by_slot=dict(Counter(m.slot.value for m in filled)),
        unavailable_slots=len(out.meals) - len(filled),
        feedback_on_plan={
            k: states.get(k, 0) for k in ("favourite", "like", "skip", "dislike", "none")
        },
        **base,
    )
