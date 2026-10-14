"""Meal plans, grocery list, feedback and dashboard endpoints (user-scoped)."""

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.plan import (
    DashboardOut,
    FeedbackIn,
    FeedbackOut,
    GroceryListOut,
    MealDetailOut,
    MealPlanOut,
    ReplaceIn,
    ReplaceResultOut,
)
from app.services import dashboard_service, feedback_service, grocery_service, meal_plan_service

router = APIRouter()


@router.post(
    "/meal-plans/generate",
    response_model=MealPlanOut,
    status_code=status.HTTP_201_CREATED,
    tags=["meal plans"],
    summary="Generate a new weekly plan (UC-06)",
)
def generate_plan(user: CurrentUser, db: DbSession) -> MealPlanOut:
    return meal_plan_service.generate(db, user)


@router.get("/meal-plans/current", response_model=MealPlanOut, tags=["meal plans"])
def current_plan(user: CurrentUser, db: DbSession) -> MealPlanOut:
    return meal_plan_service.current_plan(db, user)


@router.get(
    "/meal-plans/current/meals/{planned_meal_id}", response_model=MealDetailOut, tags=["meal plans"]
)
def meal_detail(planned_meal_id: int, user: CurrentUser, db: DbSession) -> MealDetailOut:
    return meal_plan_service.meal_detail(db, user, planned_meal_id)


@router.post(
    "/meal-plans/current/meals/{planned_meal_id}/replace",
    response_model=ReplaceResultOut,
    tags=["meal plans"],
    summary="Replace one meal (UC-10)",
)
def replace_meal(
    planned_meal_id: int, user: CurrentUser, db: DbSession, data: ReplaceIn | None = None
) -> ReplaceResultOut:
    avoid = frozenset(data.avoid_recipe_ids) if data else frozenset()
    return meal_plan_service.replace_meal(db, user, planned_meal_id, avoid)


@router.get("/grocery-lists/current", response_model=GroceryListOut, tags=["grocery list"])
def current_grocery_list(user: CurrentUser, db: DbSession) -> GroceryListOut:
    return grocery_service.current_list(db, user)


@router.post(
    "/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED, tags=["feedback"]
)
def submit_feedback(data: FeedbackIn, user: CurrentUser, db: DbSession) -> FeedbackOut:
    return feedback_service.submit(db, user, data)


@router.get("/dashboard", response_model=DashboardOut, tags=["dashboard"])
def dashboard(user: CurrentUser, db: DbSession) -> DashboardOut:
    return dashboard_service.summary(db, user)
