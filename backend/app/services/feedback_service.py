"""Feedback processing (UC-11, REQ-4.4.1 – REQ-4.4.4, Description §10.3)."""

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Feedback, MealPlan, PlannedMeal, User
from app.models.enums import FeedbackType
from app.rule_engine.config import FEEDBACK_WEIGHTS
from app.schemas.plan import FeedbackIn, FeedbackOut


def submit(db: Session, user: User, data: FeedbackIn) -> FeedbackOut:
    meal = db.scalar(
        select(PlannedMeal)
        .join(MealPlan)
        .where(PlannedMeal.id == data.planned_meal_id, MealPlan.user_id == user.id)
    )
    if meal is None:  # other users' meals are indistinguishable from missing ones
        raise AppError(404, "planned_meal_not_found", "Planned meal not found.")
    if meal.recipe_id is None:
        raise AppError(409, "no_meal", "This slot has no meal to give feedback on.")
    event = Feedback(
        user_id=user.id,
        recipe_id=meal.recipe_id,
        planned_meal_id=meal.id,
        feedback_type=data.feedback_type,
        score=FEEDBACK_WEIGHTS[data.feedback_type],
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return FeedbackOut.model_validate(event, from_attributes=True)


def _latest_events(db: Session, user_id: int) -> list[Feedback]:
    """Latest event per (planned meal, recipe): repeated clicks change, not stack, the score."""
    events = db.scalars(
        select(Feedback)
        .where(Feedback.user_id == user_id)
        .order_by(Feedback.created_at, Feedback.id)
    ).all()
    latest: dict[tuple[int | None, int, int], Feedback] = {}
    for e in events:
        key = (e.planned_meal_id, e.recipe_id, e.id if e.planned_meal_id is None else 0)
        latest[key] = e
    return list(latest.values())


def preference_scores(db: Session, user_id: int) -> dict[int, int]:
    """Weighted score per recipe (Favourite +3, Like +1, Skip −1, Dislike −3)."""
    scores: dict[int, int] = defaultdict(int)
    for e in _latest_events(db, user_id):
        scores[e.recipe_id] += e.score
    return dict(scores)


def favourite_recipe_ids(db: Session, user_id: int) -> set[int]:
    """Recipes whose most recent feedback from this user is Favourite."""
    events = db.scalars(
        select(Feedback)
        .where(Feedback.user_id == user_id)
        .order_by(Feedback.created_at, Feedback.id)
    ).all()
    latest: dict[int, FeedbackType] = {}
    for e in events:
        latest[e.recipe_id] = e.feedback_type
    return {rid for rid, t in latest.items() if t is FeedbackType.FAVOURITE}


def states_for_plan(db: Session, plan_id: int) -> dict[int, FeedbackType]:
    """Current feedback per planned meal (for the meal's current recipe)."""
    rows = db.execute(
        select(
            Feedback.planned_meal_id,
            Feedback.recipe_id,
            Feedback.feedback_type,
            PlannedMeal.recipe_id,
        )
        .join(PlannedMeal, PlannedMeal.id == Feedback.planned_meal_id)
        .where(PlannedMeal.meal_plan_id == plan_id)
        .order_by(Feedback.created_at, Feedback.id)
    ).all()
    states: dict[int, FeedbackType] = {}
    for planned_id, recipe_id, feedback_type, current_recipe in rows:
        if recipe_id == current_recipe:
            states[planned_id] = feedback_type
    return states
