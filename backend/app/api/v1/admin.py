"""Admin panel API (REQ-4.7.1 – REQ-4.7.5). Every route requires the Administrator role."""

from fastapi import APIRouter, Depends, Response, status

from app.core.deps import DbSession, require_admin
from app.core.errors import AppError
from app.schemas.catalogue import (
    FOOD_GROUPS,
    CategoryIn,
    CategoryOut,
    FoodIn,
    FoodOut,
    NutritionIn,
    RecipeIn,
    RecipeOut,
)
from app.services import catalogue_service as svc

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/food-groups", response_model=list[str])
def food_groups() -> list[str]:
    return FOOD_GROUPS


# Foods (REQ-4.7.2)
@router.get("/foods", response_model=list[FoodOut])
def list_foods(db: DbSession) -> list[FoodOut]:
    return svc.list_foods(db)


@router.post("/foods", response_model=FoodOut, status_code=status.HTTP_201_CREATED)
def create_food(data: FoodIn, db: DbSession) -> FoodOut:
    return svc.create_food(db, data)


@router.put("/foods/{food_id}", response_model=FoodOut)
def update_food(food_id: int, data: FoodIn, db: DbSession) -> FoodOut:
    return svc.update_food(db, food_id, data)


@router.delete("/foods/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food(food_id: int, db: DbSession) -> Response:
    svc.delete_food(db, food_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Nutrition values (REQ-4.7.4)
@router.get("/nutrition", response_model=list[FoodOut])
def list_nutrition(db: DbSession) -> list[FoodOut]:
    return svc.list_nutrition(db)


@router.put("/foods/{food_id}/nutrition", response_model=FoodOut)
def upsert_nutrition(food_id: int, data: NutritionIn, db: DbSession) -> FoodOut:
    return svc.upsert_nutrition(db, food_id, data)


@router.delete("/foods/{food_id}/nutrition", status_code=status.HTTP_204_NO_CONTENT)
def delete_nutrition(food_id: int, db: DbSession) -> Response:
    svc.delete_nutrition(db, food_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Recipes (REQ-4.7.3)
@router.get("/recipes", response_model=list[RecipeOut])
def list_recipes(db: DbSession) -> list[RecipeOut]:
    return svc.list_recipes(db)


@router.get("/recipes/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: DbSession) -> RecipeOut:
    return svc.recipe_out(svc.get_recipe(db, recipe_id))


@router.post("/recipes", response_model=RecipeOut, status_code=status.HTTP_201_CREATED)
def create_recipe(data: RecipeIn, db: DbSession) -> RecipeOut:
    return svc.create_recipe(db, data)


@router.put("/recipes/{recipe_id}", response_model=RecipeOut)
def update_recipe(recipe_id: int, data: RecipeIn, db: DbSession) -> RecipeOut:
    return svc.update_recipe(db, recipe_id, data)


@router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: int, db: DbSession) -> Response:
    svc.delete_recipe(db, recipe_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Categories (REQ-4.7.5, OD-02: the four categories are fixed – rename only)
@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: DbSession) -> list[CategoryOut]:
    return svc.list_categories(db)


@router.put("/categories/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, data: CategoryIn, db: DbSession) -> CategoryOut:
    return svc.update_category(db, category_id, data)


@router.post("/categories", status_code=status.HTTP_409_CONFLICT)
def create_category() -> None:
    raise AppError(409, "fixed_categories", svc.FIXED_CATEGORIES_MESSAGE)


@router.delete("/categories/{category_id}", status_code=status.HTTP_409_CONFLICT)
def delete_category(category_id: int) -> None:
    raise AppError(409, "fixed_categories", svc.FIXED_CATEGORIES_MESSAGE)
