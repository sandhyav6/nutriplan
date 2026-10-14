"""Weekly meal plans (UC-06, UC-07, UC-10): generation, retrieval and meal replacement.

Every plan and every replacement passes the independent validator before it is stored.
"""

import json
import logging
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.models import Food, MealPlan, PlannedMeal, Recipe, RecipeIngredient, User, UserProfile
from app.models.enums import MealPlanStatus
from app.repositories import profiles as profile_repo
from app.rule_engine import config
from app.rule_engine.planner import PlannerInput, find_replacement, generate_weekly_plan
from app.rule_engine.types import Infeasibility, PlannedSlot, Portion
from app.rule_engine.validator import validate_slots
from app.schemas.plan import (
    DayTotals,
    IngredientLine,
    MealDetailOut,
    MealPlanOut,
    MealSummary,
    PlannedMealOut,
    PlanNoteOut,
    ReplaceResultOut,
)
from app.schemas.profile import NutritionTargetOut
from app.services import catalogue_service, feedback_service, grocery_service
from app.services.profile_service import nutrition_for, to_profile_input

logger = logging.getLogger("nutriplan.plans")
ONE = Decimal("1")
TWO = Decimal("0.01")


def _q(value: float | Decimal, places: Decimal = TWO) -> Decimal:
    return Decimal(str(value)).quantize(places, rounding=ROUND_HALF_UP)


def week_start(today: date | None = None) -> date:
    """Plans start on Monday of the current week (OD-18)."""
    today = today or datetime.now(UTC).date()
    return today - timedelta(days=today.weekday())


def _require_profile(db: Session, user: User) -> UserProfile:
    profile = profile_repo.get_for_user(db, user.id)
    if profile is None:
        raise AppError(409, "profile_required", "Create your profile before generating a plan.")
    return profile


def _plan_query():  # type: ignore[no-untyped-def]
    return select(MealPlan).options(
        selectinload(MealPlan.planned_meals)
        .selectinload(PlannedMeal.recipe)
        .options(
            selectinload(Recipe.nutrition),
            selectinload(Recipe.category),
            selectinload(Recipe.ingredients)
            .selectinload(RecipeIngredient.food)
            .selectinload(Food.allergens),
        )
    )


def get_active_plan(db: Session, user: User) -> MealPlan | None:
    return db.scalar(
        _plan_query()
        .where(MealPlan.user_id == user.id, MealPlan.status == MealPlanStatus.ACTIVE)
        .order_by(MealPlan.id.desc())
    )


def _planner_input(
    db: Session, user: User, profile: UserProfile, recent: frozenset[int]
) -> PlannerInput:
    return PlannerInput(
        profile=to_profile_input(profile),
        target=nutrition_for(profile),
        candidates=catalogue_service.load_candidates(db),
        feedback_scores=feedback_service.preference_scores(db, user.id),
        favourite_ids=frozenset(feedback_service.favourite_recipe_ids(db, user.id)),
        recent_recipe_ids=recent,
    )


def generate(db: Session, user: User) -> MealPlanOut:
    profile = _require_profile(db, user)
    previous = get_active_plan(db, user)
    recent = (
        frozenset(m.recipe_id for m in previous.planned_meals if m.recipe_id)
        if previous
        else frozenset()
    )
    inp = _planner_input(db, user, profile, recent)
    if not inp.candidates:
        raise AppError(
            409,
            "catalogue_empty",
            "The recipe catalogue is empty. An administrator must add recipes first.",
        )

    result = generate_weekly_plan(inp)
    if isinstance(result, Infeasibility):
        raise AppError(
            422,
            result.code,
            result.message,
            {"minimum_weekly_cost_inr": result.minimum_weekly_cost_inr},
        )
    validation = validate_slots(result.slots, inp.profile)
    if not validation.is_valid:  # defence in depth – must never happen
        logger.error(
            "planner produced an invalid plan", extra={"violations": validation.violations}
        )
        raise AppError(
            500, "plan_validation_failed", "The generated plan failed validation and was discarded."
        )

    if previous is not None:
        previous.status = MealPlanStatus.ARCHIVED
    plan = MealPlan(
        user_id=user.id,
        week_start_date=week_start(),
        total_calories_kcal=_q(result.total_calories_kcal),
        total_cost_inr=_q(result.total_cost_inr),
        notes=json.dumps([{"code": n.code, "message": n.message} for n in result.notes]),
    )
    for s in result.slots:
        plan.planned_meals.append(
            PlannedMeal(
                day_of_week=s.day_of_week,
                slot=s.slot,
                recipe_id=s.portion.candidate.recipe_id if s.portion else None,
                servings=s.portion.servings if s.portion else ONE,
                unavailable_reason=s.unavailable_reason,
            )
        )
    db.add(plan)
    db.flush()
    grocery_service.regenerate(db, plan)  # UC-06 step 5
    db.commit()
    return current_plan(db, user)


# ------------------------------------------------------------------ output
def _summary(meal: PlannedMeal) -> MealSummary | None:
    recipe = meal.recipe
    if recipe is None or recipe.nutrition is None:
        return None
    n, s = recipe.nutrition, meal.servings
    return MealSummary(
        recipe_id=recipe.id,
        name=recipe.name,
        prep_time_min=recipe.prep_time_min,
        diet_type=catalogue_service.recipe_diet_type(recipe),
        servings=s,
        calories_kcal=_q(n.calories_kcal * s, ONE),
        protein_g=_q(n.protein_g * s, Decimal("0.1")),
        carbs_g=_q(n.carbs_g * s, Decimal("0.1")),
        fat_g=_q(n.fat_g * s, Decimal("0.1")),
        cost_inr=_q(n.estimated_cost_inr * s),
    )


def _meal_out(plan: MealPlan, meal: PlannedMeal, states: dict) -> PlannedMealOut:  # type: ignore[type-arg]
    return PlannedMealOut(
        id=meal.id,
        day_of_week=meal.day_of_week,
        date=plan.week_start_date + timedelta(days=meal.day_of_week),
        slot=meal.slot,
        meal=_summary(meal),
        unavailable_reason=meal.unavailable_reason,
        feedback=states.get(meal.id),
    )


def _sorted_meals(plan: MealPlan) -> list[PlannedMeal]:
    order = {slot: i for i, slot in enumerate(config.MEAL_SLOTS)}
    return sorted(plan.planned_meals, key=lambda m: (m.day_of_week, order[m.slot]))


def plan_out(db: Session, user: User, plan: MealPlan) -> MealPlanOut:
    profile = _require_profile(db, user)
    states = feedback_service.states_for_plan(db, plan.id)
    meals = [_meal_out(plan, m, states) for m in _sorted_meals(plan)]
    days = []
    for day in range(config.DAYS_PER_PLAN):
        summaries = [m.meal for m in meals if m.day_of_week == day and m.meal]
        days.append(
            DayTotals(
                day_of_week=day,
                date=plan.week_start_date + timedelta(days=day),
                calories_kcal=sum((x.calories_kcal for x in summaries), Decimal("0")),
                protein_g=sum((x.protein_g for x in summaries), Decimal("0")),
                cost_inr=sum((x.cost_inr for x in summaries), Decimal("0")),
            )
        )
    nutrition = nutrition_for(profile)
    generated = (
        plan.generated_at if plan.generated_at.tzinfo else plan.generated_at.replace(tzinfo=UTC)
    )
    updated = (
        profile.updated_at if profile.updated_at.tzinfo else profile.updated_at.replace(tzinfo=UTC)
    )
    return MealPlanOut(
        id=plan.id,
        week_start_date=plan.week_start_date,
        generated_at=plan.generated_at,
        total_calories_kcal=plan.total_calories_kcal or Decimal("0"),
        total_cost_inr=plan.total_cost_inr or Decimal("0"),
        weekly_budget_inr=profile.weekly_budget_inr,
        nutrition=NutritionTargetOut(**asdict(nutrition)),
        notes=[PlanNoteOut(**n) for n in json.loads(plan.notes or "[]")],
        profile_changed_since_generation=updated > generated,
        meals=meals,
        days=days,
    )


def current_plan(db: Session, user: User) -> MealPlanOut:
    db.expire_all()
    plan = get_active_plan(db, user)
    if plan is None:
        raise AppError(
            404, "plan_not_found", "You have no meal plan yet. Generate one to get started."
        )
    return plan_out(db, user, plan)


def _get_meal(db: Session, user: User, planned_meal_id: int) -> tuple[MealPlan, PlannedMeal]:
    plan = get_active_plan(db, user)
    meal = next((m for m in plan.planned_meals if m.id == planned_meal_id), None) if plan else None
    if plan is None or meal is None:
        raise AppError(
            404, "planned_meal_not_found", "Planned meal not found in your current plan."
        )
    return plan, meal


def meal_detail(db: Session, user: User, planned_meal_id: int) -> MealDetailOut:
    plan, meal = _get_meal(db, user, planned_meal_id)
    base = _meal_out(plan, meal, feedback_service.states_for_plan(db, plan.id))
    recipe = meal.recipe
    n = recipe.nutrition if recipe else None
    return MealDetailOut(
        **base.model_dump(),
        description=recipe.description if recipe else None,
        category_name=recipe.category.name if recipe else None,
        allergens=catalogue_service.recipe_allergen_names(recipe) if recipe else [],
        ingredients=[
            IngredientLine(
                food_id=i.food_id,
                name=i.food.name,
                quantity=_q(i.quantity * meal.servings),
                unit=i.unit,
                food_group=i.food.food_group,
            )
            for i in (recipe.ingredients if recipe else [])
        ],
        sugar_g=_q((n.sugar_g or 0) * meal.servings, Decimal("0.1")) if n else None,
        fibre_g=_q((n.fibre_g or 0) * meal.servings, Decimal("0.1")) if n else None,
    )


def _slots_from_plan(plan: MealPlan) -> tuple[list[PlannedMeal], list[PlannedSlot]]:
    meals = _sorted_meals(plan)
    slots = []
    for m in meals:
        candidate = catalogue_service.to_candidate(m.recipe) if m.recipe else None
        portion = Portion(candidate, m.servings) if candidate else None
        slots.append(PlannedSlot(m.day_of_week, m.slot, portion, m.unavailable_reason))
    return meals, slots


def replace_meal(
    db: Session, user: User, planned_meal_id: int, avoid_recipe_ids: frozenset[int] = frozenset()
) -> ReplaceResultOut:
    """UC-10 – swap one meal, keep every constraint, regenerate the grocery list (REQ-4.3.3)."""
    profile = _require_profile(db, user)
    plan, _ = _get_meal(db, user, planned_meal_id)
    meals, slots = _slots_from_plan(plan)
    index = next(i for i, m in enumerate(meals) if m.id == planned_meal_id)
    inp = _planner_input(db, user, profile, frozenset())
    result = find_replacement(inp, slots, index, avoid_recipe_ids)
    if result.portion is None:
        raise AppError(409, "no_replacement", result.reason or "No valid replacement exists.")

    new_slots = list(slots)
    new_slots[index] = PlannedSlot(slots[index].day_of_week, slots[index].slot, result.portion)
    check = validate_slots(new_slots, inp.profile)
    if not check.is_valid:
        raise AppError(500, "plan_validation_failed", "The replacement failed validation.")

    meal = meals[index]
    meal.recipe = db.get(Recipe, result.portion.candidate.recipe_id)
    meal.servings = result.portion.servings
    meal.unavailable_reason = None
    plan.total_calories_kcal = _q(sum(s.portion.calories_kcal for s in new_slots if s.portion))
    plan.total_cost_inr = _q(
        sum((s.portion.cost_inr for s in new_slots if s.portion), Decimal("0"))
    )
    db.flush()
    grocery_service.regenerate(db, plan)
    db.commit()
    db.expire_all()
    return ReplaceResultOut(
        meal=meal_detail(db, user, planned_meal_id),
        total_calories_kcal=plan.total_calories_kcal,
        total_cost_inr=plan.total_cost_inr,
    )
