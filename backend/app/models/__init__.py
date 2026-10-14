"""SQLAlchemy models. Importing this package registers every table on Base.metadata."""

from app.db.base import Base
from app.models.catalog import (
    Allergen,
    Food,
    FoodNutrition,
    MealCategory,
    Recipe,
    RecipeIngredient,
    RecipeNutrition,
    food_allergens,
)
from app.models.feedback import Feedback
from app.models.meal_plan import GroceryList, GroceryListItem, MealPlan, PlannedMeal
from app.models.session import UserSession
from app.models.user import User, UserProfile, user_profile_allergens, user_profile_excluded_foods

__all__ = [
    "Allergen",
    "Base",
    "Feedback",
    "Food",
    "FoodNutrition",
    "GroceryList",
    "GroceryListItem",
    "MealCategory",
    "MealPlan",
    "PlannedMeal",
    "Recipe",
    "RecipeIngredient",
    "RecipeNutrition",
    "User",
    "UserProfile",
    "UserSession",
    "food_allergens",
    "user_profile_allergens",
    "user_profile_excluded_foods",
]
