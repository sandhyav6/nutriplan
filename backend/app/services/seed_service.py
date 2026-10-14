"""Loads the illustrative development catalogue (OD-15). Idempotent: skips if foods exist."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Allergen, Food, FoodNutrition, MealCategory, Recipe, RecipeIngredient
from app.models.enums import DietType, MealSlot, MeasurementUnit
from app.seed.catalogue_data import FOODS, RECIPES
from app.services.catalogue_service import get_recipe, recalculate_recipe


def _d(value: float | int) -> Decimal:
    return Decimal(str(value))


def seed_catalogue(db: Session) -> dict[str, int]:
    if db.scalar(select(func.count()).select_from(Food)):
        return {"foods": 0, "recipes": 0}

    allergens = {a.name: a for a in db.scalars(select(Allergen))}
    categories = {c.slot: c for c in db.scalars(select(MealCategory))}
    if len(categories) != 4 or not allergens:
        raise RuntimeError("Reference data missing – run `python -m alembic upgrade head` first.")

    foods: dict[str, Food] = {}
    for name, group, diet, unit, price, price_qty, allergen_names, per_qty, n in FOODS:
        food = Food(
            name=name,
            food_group=group,
            diet_type=DietType(diet),
            unit=MeasurementUnit(unit),
            price_inr=_d(price),
            price_quantity=_d(price_qty),
            allergens=[allergens[a] for a in allergen_names],
        )
        food.nutrition = FoodNutrition(
            per_quantity=_d(per_qty),
            calories_kcal=_d(n[0]),
            protein_g=_d(n[1]),
            carbs_g=_d(n[2]),
            fat_g=_d(n[3]),
            fibre_g=_d(n[4]),
            sugar_g=_d(n[5]),
            sodium_mg=_d(n[6]),
            cholesterol_mg=_d(n[7]),
        )
        db.add(food)
        foods[name] = food
    db.flush()

    recipe_ids: list[int] = []
    for name, slot, prep, ingredients in RECIPES:
        recipe = Recipe(
            name=name,
            category_id=categories[MealSlot(slot)].id,
            prep_time_min=prep,
            description="Illustrative development recipe.",
        )
        for food_name, quantity in ingredients:
            food = foods[food_name]
            recipe.ingredients.append(
                RecipeIngredient(food=food, quantity=_d(quantity), unit=food.unit)
            )
        db.add(recipe)
        db.flush()
        recipe_ids.append(recipe.id)

    for recipe_id in recipe_ids:
        recalculate_recipe(db, get_recipe(db, recipe_id))
    db.commit()
    return {"foods": len(foods), "recipes": len(recipe_ids)}
