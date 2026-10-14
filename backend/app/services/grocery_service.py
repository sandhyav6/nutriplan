"""Grocery list generation (UC-08/09, REQ-4.3.1 – REQ-4.3.4).

Ingredients of every planned meal are scaled by the meal's servings, identical foods are
combined (200 g + 300 g = 500 g), duplicates removed and quantities shown in readable units.
"""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.models import (
    Food,
    GroceryList,
    GroceryListItem,
    MealPlan,
    PlannedMeal,
    Recipe,
    RecipeIngredient,
    User,
)
from app.models.enums import MealPlanStatus, MeasurementUnit
from app.schemas.plan import GroceryGroupOut, GroceryItemOut, GroceryListOut

TWO = Decimal("0.01")


def aggregate(lines: list[tuple[Food, Decimal]]) -> dict[int, tuple[Food, Decimal]]:
    """Combine (food, quantity) pairs into one total per food."""
    totals: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    foods: dict[int, Food] = {}
    for food, quantity in lines:
        totals[food.id] += quantity
        foods[food.id] = food
    return {fid: (foods[fid], qty) for fid, qty in totals.items()}


def display_quantity(quantity: Decimal, unit: MeasurementUnit) -> str:
    """REQ-4.3.4 – consistent, human-readable units."""

    def fmt(value: Decimal) -> str:
        text = f"{value.quantize(TWO, rounding=ROUND_HALF_UP):,.2f}".rstrip("0").rstrip(".")
        return text or "0"

    def whole(value: Decimal) -> str:
        return str(max(1, int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))))

    if unit is MeasurementUnit.GRAM:
        return f"{fmt(quantity / 1000)} kg" if quantity >= 1000 else f"{whole(quantity)} g"
    if unit is MeasurementUnit.MILLILITRE:
        return f"{fmt(quantity / 1000)} L" if quantity >= 1000 else f"{whole(quantity)} ml"
    pieces = quantity.quantize(Decimal("1"), rounding="ROUND_CEILING")
    return f"{pieces} {'piece' if pieces == 1 else 'pieces'}"


def regenerate(db: Session, plan: MealPlan) -> GroceryList:
    meals = db.scalars(
        select(PlannedMeal)
        .where(PlannedMeal.meal_plan_id == plan.id, PlannedMeal.recipe_id.is_not(None))
        .options(
            selectinload(PlannedMeal.recipe)
            .selectinload(Recipe.ingredients)
            .selectinload(RecipeIngredient.food)
        )
        .execution_options(populate_existing=True)  # never reuse stale cached relationships
    ).all()
    lines = [
        (ing.food, ing.quantity * meal.servings / Decimal(meal.recipe.servings or 1))
        for meal in meals
        for ing in meal.recipe.ingredients
    ]
    existing = db.scalar(select(GroceryList).where(GroceryList.meal_plan_id == plan.id))
    if existing is not None:
        db.delete(existing)
        db.flush()

    grocery = GroceryList(meal_plan_id=plan.id, total_estimated_cost_inr=Decimal("0"))
    total = Decimal("0")
    for food, quantity in aggregate(lines).values():
        cost = (quantity / food.price_quantity * food.price_inr).quantize(
            TWO, rounding=ROUND_HALF_UP
        )
        total += cost
        grocery.items.append(
            GroceryListItem(
                food_id=food.id,
                quantity=quantity.quantize(TWO, rounding=ROUND_HALF_UP),
                unit=food.unit,
                estimated_cost_inr=cost,
            )
        )
    grocery.total_estimated_cost_inr = total
    db.add(grocery)
    db.flush()
    return grocery


def current_list(db: Session, user: User) -> GroceryListOut:
    plan = db.scalar(
        select(MealPlan)
        .where(MealPlan.user_id == user.id, MealPlan.status == MealPlanStatus.ACTIVE)
        .order_by(MealPlan.id.desc())
    )
    if plan is None:
        raise AppError(404, "plan_not_found", "Generate a weekly meal plan to get a grocery list.")
    grocery = db.scalar(
        select(GroceryList)
        .where(GroceryList.meal_plan_id == plan.id)
        .options(selectinload(GroceryList.items).selectinload(GroceryListItem.food))
    )
    if grocery is None:
        grocery = regenerate(db, plan)
        db.commit()
        db.refresh(grocery)

    groups: dict[str, list[GroceryItemOut]] = defaultdict(list)
    for item in sorted(grocery.items, key=lambda i: i.food.name):
        groups[item.food.food_group].append(
            GroceryItemOut(
                food_id=item.food_id,
                name=item.food.name,
                food_group=item.food.food_group,
                quantity=item.quantity,
                unit=item.unit,
                display_quantity=display_quantity(item.quantity, item.unit),
                estimated_cost_inr=item.estimated_cost_inr,
            )
        )
    profile = user.profile
    return GroceryListOut(
        id=grocery.id,
        meal_plan_id=plan.id,
        week_start_date=plan.week_start_date,
        generated_at=grocery.generated_at,
        total_estimated_cost_inr=grocery.total_estimated_cost_inr,
        weekly_budget_inr=profile.weekly_budget_inr if profile else Decimal("0"),
        item_count=len(grocery.items),
        groups=[
            GroceryGroupOut(
                food_group=name,
                items=items,
                subtotal_inr=sum((i.estimated_cost_inr for i in items), Decimal("0")),
            )
            for name, items in sorted(groups.items())
        ],
    )
