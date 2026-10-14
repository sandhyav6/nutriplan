"""Food / recipe catalogue: admin CRUD (UC-13 – UC-16), recipe nutrition pre-calculation and
conversion of recipes into rule-engine candidates."""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.models import (
    Allergen,
    Food,
    FoodNutrition,
    MealCategory,
    PlannedMeal,
    Recipe,
    RecipeIngredient,
    RecipeNutrition,
)
from app.models.enums import DietType
from app.rule_engine import config
from app.rule_engine.types import MealCandidate
from app.schemas.catalogue import (
    CategoryIn,
    CategoryOut,
    FoodIn,
    FoodOut,
    IngredientOut,
    NutritionIn,
    NutritionOut,
    RecipeIn,
    RecipeNutritionOut,
    RecipeOut,
)
from app.schemas.profile import NamedRef

DIET_LEVEL = {
    DietType.VEGAN: 0,
    DietType.VEGETARIAN: 1,
    DietType.EGGETARIAN: 2,
    DietType.NON_VEGETARIAN: 3,
}
DIET_BY_LEVEL = {level: diet for diet, level in DIET_LEVEL.items()}
TWO_PLACES = Decimal("0.01")


def _q(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


# ------------------------------------------------------------------ queries
def _recipe_query():  # type: ignore[no-untyped-def]
    return select(Recipe).options(
        selectinload(Recipe.category),
        selectinload(Recipe.nutrition),
        selectinload(Recipe.ingredients)
        .selectinload(RecipeIngredient.food)
        .selectinload(Food.allergens),
    )


def _food_query():  # type: ignore[no-untyped-def]
    return select(Food).options(selectinload(Food.allergens), selectinload(Food.nutrition))


def get_recipe(db: Session, recipe_id: int) -> Recipe:
    recipe = db.scalar(_recipe_query().where(Recipe.id == recipe_id))
    if recipe is None:
        raise AppError(404, "recipe_not_found", "Recipe not found.")
    return recipe


def get_food(db: Session, food_id: int) -> Food:
    food = db.scalar(_food_query().where(Food.id == food_id))
    if food is None:
        raise AppError(404, "food_not_found", "Food not found.")
    return food


# ------------------------------------------------------- derived properties
def recipe_diet_type(recipe: Recipe) -> DietType:
    """A recipe is as restrictive as its least restrictive ingredient."""
    level = max((DIET_LEVEL[i.food.diet_type] for i in recipe.ingredients), default=0)
    return DIET_BY_LEVEL[level]


def recipe_allergen_names(recipe: Recipe) -> list[str]:
    return sorted({a.name for i in recipe.ingredients for a in i.food.allergens})


def calculate_recipe_nutrition(recipe: Recipe) -> dict[str, Decimal]:
    """Per-serving nutrition and cost from ingredients (SRS §2.7: values pre-calculated)."""
    totals = dict.fromkeys(
        ("calories_kcal", "protein_g", "carbs_g", "fat_g", "fibre_g", "sugar_g"), Decimal("0")
    )
    cost = Decimal("0")
    for ingredient in recipe.ingredients:
        food = ingredient.food
        cost += ingredient.quantity / food.price_quantity * food.price_inr
        nutrition = food.nutrition
        if nutrition is None:
            continue
        ratio = ingredient.quantity / nutrition.per_quantity
        totals["calories_kcal"] += nutrition.calories_kcal * ratio
        totals["protein_g"] += nutrition.protein_g * ratio
        totals["carbs_g"] += nutrition.carbs_g * ratio
        totals["fat_g"] += nutrition.fat_g * ratio
        totals["fibre_g"] += (nutrition.fibre_g or Decimal("0")) * ratio
        totals["sugar_g"] += (nutrition.sugar_g or Decimal("0")) * ratio
    servings = Decimal(recipe.servings or 1)
    result = {key: _q(value / servings) for key, value in totals.items()}
    result["estimated_cost_inr"] = _q(cost / servings)
    return result


def recalculate_recipe(db: Session, recipe: Recipe) -> None:
    values = calculate_recipe_nutrition(recipe)
    if recipe.nutrition is None:
        recipe.nutrition = RecipeNutrition(**values)
    else:
        for key, value in values.items():
            setattr(recipe.nutrition, key, value)
        recipe.nutrition.calculated_at = func.now()


def recalculate_recipes_using_food(db: Session, food_id: int) -> int:
    ids = db.scalars(
        select(RecipeIngredient.recipe_id).where(RecipeIngredient.food_id == food_id).distinct()
    ).all()
    for recipe_id in ids:
        db.expire_all()
        recalculate_recipe(db, get_recipe(db, recipe_id))
        db.flush()
    return len(ids)


# --------------------------------------------------------------- engine view
def load_candidates(db: Session) -> list[MealCandidate]:
    """Active recipes with pre-calculated nutrition, as rule-engine candidates."""
    recipes = db.scalars(_recipe_query().where(Recipe.is_active.is_(True)).order_by(Recipe.id))
    return [c for r in recipes if (c := to_candidate(r)) is not None]


def to_candidate(recipe: Recipe) -> MealCandidate | None:
    n = recipe.nutrition
    if n is None or not recipe.ingredients:
        return None
    groups = {i.food.food_group for i in recipe.ingredients}
    return MealCandidate(
        recipe_id=recipe.id,
        name=recipe.name,
        slot=recipe.category.slot,
        category_id=recipe.category_id,
        diet_type=recipe_diet_type(recipe),
        prep_time_min=recipe.prep_time_min,
        calories_kcal=float(n.calories_kcal),
        protein_g=float(n.protein_g),
        carbs_g=float(n.carbs_g),
        fat_g=float(n.fat_g),
        sugar_g=float(n.sugar_g or 0),
        fibre_g=float(n.fibre_g or 0),
        cost_inr=n.estimated_cost_inr,
        allergen_ids=frozenset(a.id for i in recipe.ingredients for a in i.food.allergens),
        food_ids=frozenset(i.food_id for i in recipe.ingredients),
        core_food_ids=frozenset(
            i.food_id
            for i in recipe.ingredients
            if i.food.food_group not in config.PANTRY_FOOD_GROUPS
        ),
        has_vegetable=config.VEGETABLE_GROUP in groups,
        has_fruit=config.FRUIT_GROUP in groups,
    )


# ----------------------------------------------------------------- DTOs
def recipe_out(recipe: Recipe) -> RecipeOut:
    return RecipeOut(
        id=recipe.id,
        name=recipe.name,
        description=recipe.description,
        category_id=recipe.category_id,
        category_name=recipe.category.name,
        slot=recipe.category.slot,
        prep_time_min=recipe.prep_time_min,
        is_active=recipe.is_active,
        diet_type=recipe_diet_type(recipe),
        allergens=recipe_allergen_names(recipe),
        ingredients=[
            IngredientOut(
                food_id=i.food_id,
                food_name=i.food.name,
                quantity=i.quantity,
                unit=i.unit,
                food_group=i.food.food_group,
            )
            for i in recipe.ingredients
        ],
        nutrition=RecipeNutritionOut.model_validate(recipe.nutrition) if recipe.nutrition else None,
        updated_at=recipe.updated_at,
    )


def food_out(db: Session, food: Food) -> FoodOut:
    count = db.scalar(
        select(func.count())
        .select_from(RecipeIngredient)
        .where(RecipeIngredient.food_id == food.id)
    )
    return FoodOut(
        id=food.id,
        name=food.name,
        food_group=food.food_group,
        diet_type=food.diet_type,
        unit=food.unit,
        price_inr=food.price_inr,
        price_quantity=food.price_quantity,
        allergens=[
            NamedRef.model_validate(a) for a in sorted(food.allergens, key=lambda a: a.name)
        ],
        nutrition=NutritionOut.model_validate(food.nutrition) if food.nutrition else None,
        recipe_count=count or 0,
        updated_at=food.updated_at,
    )


# ------------------------------------------------------------------- foods
def _allergens(db: Session, ids: list[int]) -> list[Allergen]:
    if not ids:
        return []
    found = list(db.scalars(select(Allergen).where(Allergen.id.in_(ids))))
    if len(found) != len(set(ids)):
        raise AppError(422, "validation_error", "One or more allergens do not exist.")
    return found


def _ensure_unique_name(db: Session, model, name: str, exclude_id: int | None = None) -> None:  # type: ignore[no-untyped-def]
    stmt = select(model.id).where(func.lower(model.name) == name.lower())
    if exclude_id is not None:
        stmt = stmt.where(model.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise AppError(409, "duplicate_name", f"“{name}” already exists.", {"field": "name"})


def list_foods(db: Session) -> list[FoodOut]:
    return [food_out(db, f) for f in db.scalars(_food_query().order_by(Food.name))]


def create_food(db: Session, data: FoodIn) -> FoodOut:
    _ensure_unique_name(db, Food, data.name)
    food = Food(**data.model_dump(exclude={"allergen_ids"}))
    food.allergens = _allergens(db, data.allergen_ids)
    db.add(food)
    db.commit()
    return food_out(db, get_food(db, food.id))


def update_food(db: Session, food_id: int, data: FoodIn) -> FoodOut:
    food = get_food(db, food_id)
    _ensure_unique_name(db, Food, data.name, exclude_id=food_id)
    if data.unit != food.unit:
        in_use = db.scalar(
            select(func.count())
            .select_from(RecipeIngredient)
            .where(RecipeIngredient.food_id == food_id)
        )
        if in_use:
            raise AppError(
                409,
                "unit_in_use",
                "The unit cannot change while recipes use this food – their quantities "
                "would be wrong.",
            )
    for key, value in data.model_dump(exclude={"allergen_ids"}).items():
        setattr(food, key, value)
    food.allergens = _allergens(db, data.allergen_ids)
    db.flush()
    recalculate_recipes_using_food(db, food_id)  # price may have changed
    db.commit()
    return food_out(db, get_food(db, food_id))


def delete_food(db: Session, food_id: int) -> None:
    food = get_food(db, food_id)
    in_use = db.scalar(
        select(func.count())
        .select_from(RecipeIngredient)
        .where(RecipeIngredient.food_id == food_id)
    )
    if in_use:
        raise AppError(
            409,
            "food_in_use",
            f"“{food.name}” is used in {in_use} recipe(s). Remove it from them first.",
        )
    db.delete(food)
    db.commit()


# --------------------------------------------------------------- nutrition
def list_nutrition(db: Session) -> list[FoodOut]:
    return list_foods(db)


def upsert_nutrition(db: Session, food_id: int, data: NutritionIn) -> FoodOut:
    food = get_food(db, food_id)
    if food.nutrition is None:
        food.nutrition = FoodNutrition(**data.model_dump())
    else:
        for key, value in data.model_dump().items():
            setattr(food.nutrition, key, value)
    db.flush()
    recalculate_recipes_using_food(db, food_id)
    db.commit()
    return food_out(db, get_food(db, food_id))


def delete_nutrition(db: Session, food_id: int) -> None:
    food = get_food(db, food_id)
    if food.nutrition is None:
        raise AppError(404, "nutrition_not_found", "This food has no nutrition values.")
    db.delete(food.nutrition)
    db.flush()
    recalculate_recipes_using_food(db, food_id)
    db.commit()


# ----------------------------------------------------------------- recipes
def list_recipes(db: Session) -> list[RecipeOut]:
    return [recipe_out(r) for r in db.scalars(_recipe_query().order_by(Recipe.name))]


def _apply_recipe(db: Session, recipe: Recipe, data: RecipeIn) -> None:
    if db.get(MealCategory, data.category_id) is None:
        raise AppError(422, "validation_error", "Unknown meal category.", {"field": "category_id"})
    foods = {
        f.id: f
        for f in db.scalars(select(Food).where(Food.id.in_([i.food_id for i in data.ingredients])))
    }
    missing = [i.food_id for i in data.ingredients if i.food_id not in foods]
    if missing:
        raise AppError(422, "validation_error", "One or more ingredients do not exist.")
    recipe.name = data.name
    recipe.description = data.description
    recipe.category_id = data.category_id
    recipe.prep_time_min = data.prep_time_min
    recipe.is_active = data.is_active
    recipe.ingredients.clear()
    db.flush()
    for item in data.ingredients:
        food = foods[item.food_id]
        # Quantities are always stored in the food's canonical unit.
        recipe.ingredients.append(
            RecipeIngredient(food=food, quantity=item.quantity, unit=food.unit)
        )


def create_recipe(db: Session, data: RecipeIn) -> RecipeOut:
    _ensure_unique_name(db, Recipe, data.name)
    recipe = Recipe(name=data.name, category_id=data.category_id, prep_time_min=data.prep_time_min)
    db.add(recipe)
    _apply_recipe(db, recipe, data)
    db.flush()
    recalculate_recipe(db, get_recipe(db, recipe.id))
    db.commit()
    return recipe_out(get_recipe(db, recipe.id))


def update_recipe(db: Session, recipe_id: int, data: RecipeIn) -> RecipeOut:
    recipe = get_recipe(db, recipe_id)
    _ensure_unique_name(db, Recipe, data.name, exclude_id=recipe_id)
    _apply_recipe(db, recipe, data)
    db.flush()
    db.expire_all()
    recalculate_recipe(db, get_recipe(db, recipe_id))
    db.commit()
    return recipe_out(get_recipe(db, recipe_id))


def delete_recipe(db: Session, recipe_id: int) -> None:
    recipe = get_recipe(db, recipe_id)
    used = db.scalar(
        select(func.count()).select_from(PlannedMeal).where(PlannedMeal.recipe_id == recipe_id)
    )
    if used:
        raise AppError(
            409,
            "recipe_in_use",
            f"“{recipe.name}” appears in {used} planned meal(s). Deactivate it instead so it is "
            "no longer recommended.",
        )
    db.delete(recipe)
    db.commit()


# -------------------------------------------------------------- categories
def list_categories(db: Session) -> list[CategoryOut]:
    counts = dict(
        db.execute(select(Recipe.category_id, func.count()).group_by(Recipe.category_id)).all()
    )
    return [
        CategoryOut.model_validate(c).model_copy(update={"recipe_count": counts.get(c.id, 0)})
        for c in db.scalars(select(MealCategory).order_by(MealCategory.display_order))
    ]


def update_category(db: Session, category_id: int, data: CategoryIn) -> CategoryOut:
    category = db.get(MealCategory, category_id)
    if category is None:
        raise AppError(404, "category_not_found", "Category not found.")
    _ensure_unique_name(db, MealCategory, data.name, exclude_id=category_id)
    category.name = data.name.strip()
    category.description = data.description
    db.commit()
    return next(c for c in list_categories(db) if c.id == category_id)


FIXED_CATEGORIES_MESSAGE = (
    "NutriPlan uses exactly four meal categories (breakfast, lunch, dinner, snack) so that "
    "every weekly plan has the same structure. You can rename them, but not add or delete them."
)
