"""Initial schema: users, profiles, catalogue, meal plans, grocery lists, feedback.

Also inserts reference data that the schema depends on:
* the four fixed meal categories (breakfast, lunch, dinner, snack)
* the allergen reference list used for structural allergy filtering

Revision ID: 0001
Revises:
Create Date: 2026-10-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _enum(table: str, name: str, *values: str) -> sa.Enum:
    """VARCHAR + CHECK constraint, named like the models' naming convention (ck_<table>_<name>)."""
    return sa.Enum(
        *values,
        name=op.f(f"ck_{table}_{name}"),
        native_enum=False,
        create_constraint=True,
        length=max(len(v) for v in values),
    )


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


DIET = ("vegan", "vegetarian", "eggetarian", "non_vegetarian")
SLOTS = ("breakfast", "lunch", "dinner", "snack")
UNITS = ("g", "ml", "piece")


def upgrade() -> None:
    # ---------------------------------------------------------------- users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            _enum("users", "user_role", "user", "admin"),
            server_default="user",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    # ------------------------------------------------------------ catalogue
    allergens = op.create_table(
        "allergens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_allergens")),
        sa.UniqueConstraint("name", name=op.f("uq_allergens_name")),
    )

    meal_categories = op.create_table(
        "meal_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slot", _enum("meal_categories", "meal_slot", *SLOTS), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("display_order", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meal_categories")),
        sa.UniqueConstraint("name", name=op.f("uq_meal_categories_name")),
        sa.UniqueConstraint("slot", name=op.f("uq_meal_categories_slot")),
    )

    op.create_table(
        "foods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("food_group", sa.String(length=50), nullable=False),
        sa.Column("diet_type", _enum("foods", "diet_type", *DIET), nullable=False),
        sa.Column("unit", _enum("foods", "measurement_unit", *UNITS), nullable=False),
        sa.Column("price_inr", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("price_quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("price_inr >= 0", name=op.f("ck_foods_price_non_negative")),
        sa.CheckConstraint("price_quantity > 0", name=op.f("ck_foods_price_quantity_positive")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_foods")),
        sa.UniqueConstraint("name", name=op.f("uq_foods_name")),
    )

    op.create_table(
        "food_allergens",
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("allergen_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["allergen_id"],
            ["allergens.id"],
            name=op.f("fk_food_allergens_allergen_id_allergens"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_food_allergens_food_id_foods"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("food_id", "allergen_id", name=op.f("pk_food_allergens")),
    )

    op.create_table(
        "food_nutrition",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("per_quantity", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("calories_kcal", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("protein_g", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("carbs_g", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("fat_g", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("fibre_g", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("sugar_g", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("sodium_mg", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("cholesterol_mg", sa.Numeric(precision=8, scale=2), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "per_quantity > 0", name=op.f("ck_food_nutrition_per_quantity_positive")
        ),
        sa.CheckConstraint(
            "calories_kcal >= 0 AND protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0",
            name=op.f("ck_food_nutrition_macros_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_food_nutrition_food_id_foods"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_food_nutrition")),
        sa.UniqueConstraint("food_id", name=op.f("uq_food_nutrition_food_id")),
    )

    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("prep_time_min", sa.SmallInteger(), nullable=False),
        sa.Column("servings", sa.SmallInteger(), server_default="1", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("prep_time_min > 0", name=op.f("ck_recipes_prep_time_positive")),
        sa.CheckConstraint("servings > 0", name=op.f("ck_recipes_servings_positive")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["meal_categories.id"],
            name=op.f("fk_recipes_category_id_meal_categories"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipes")),
        sa.UniqueConstraint("name", name=op.f("uq_recipes_name")),
    )
    op.create_index(op.f("ix_recipes_category_id"), "recipes", ["category_id"], unique=False)

    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unit", _enum("recipe_ingredients", "measurement_unit", *UNITS), nullable=False),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_recipe_ingredients_quantity_positive")),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_recipe_ingredients_food_id_foods"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_recipe_ingredients_recipe_id_recipes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipe_ingredients")),
        sa.UniqueConstraint(
            "recipe_id", "food_id", name=op.f("uq_recipe_ingredients_recipe_id_food_id")
        ),
    )
    op.create_index(
        op.f("ix_recipe_ingredients_food_id"), "recipe_ingredients", ["food_id"], unique=False
    )
    op.create_index(
        op.f("ix_recipe_ingredients_recipe_id"), "recipe_ingredients", ["recipe_id"], unique=False
    )

    op.create_table(
        "recipe_nutrition",
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("calories_kcal", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("protein_g", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("carbs_g", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("fat_g", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("fibre_g", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("sugar_g", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("estimated_cost_inr", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "calories_kcal >= 0 AND protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0",
            name=op.f("ck_recipe_nutrition_macros_non_negative"),
        ),
        sa.CheckConstraint(
            "estimated_cost_inr >= 0", name=op.f("ck_recipe_nutrition_cost_non_negative")
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_recipe_nutrition_recipe_id_recipes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("recipe_id", name=op.f("pk_recipe_nutrition")),
    )

    # ------------------------------------------------------------- profiles
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("age", sa.SmallInteger(), nullable=False),
        sa.Column(
            "gender", _enum("user_profiles", "gender", "male", "female", "other"), nullable=False
        ),
        sa.Column("height_cm", sa.Numeric(precision=5, scale=1), nullable=False),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=1), nullable=False),
        sa.Column(
            "activity_level",
            _enum(
                "user_profiles", "activity_level", "sedentary", "moderately_active", "very_active"
            ),
            nullable=False,
        ),
        sa.Column(
            "dietary_preference",
            _enum("user_profiles", "dietary_preference", *DIET),
            nullable=False,
        ),
        sa.Column(
            "health_goal",
            _enum("user_profiles", "health_goal", "weight_loss", "muscle_gain", "maintenance"),
            nullable=False,
        ),
        sa.Column("weekly_budget_inr", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("max_cooking_time_min", sa.SmallInteger(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("age BETWEEN 13 AND 100", name=op.f("ck_user_profiles_age_range")),
        sa.CheckConstraint(
            "height_cm BETWEEN 100 AND 250", name=op.f("ck_user_profiles_height_range")
        ),
        sa.CheckConstraint(
            "weight_kg BETWEEN 25 AND 300", name=op.f("ck_user_profiles_weight_range")
        ),
        sa.CheckConstraint("weekly_budget_inr > 0", name=op.f("ck_user_profiles_budget_positive")),
        sa.CheckConstraint(
            "max_cooking_time_min BETWEEN 5 AND 240",
            name=op.f("ck_user_profiles_cooking_time_range"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_profiles")),
        sa.UniqueConstraint("user_id", name=op.f("uq_user_profiles_user_id")),
    )

    op.create_table(
        "user_profile_allergens",
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("allergen_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["allergen_id"],
            ["allergens.id"],
            name=op.f("fk_user_profile_allergens_allergen_id_allergens"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["user_profiles.id"],
            name=op.f("fk_user_profile_allergens_profile_id_user_profiles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "profile_id", "allergen_id", name=op.f("pk_user_profile_allergens")
        ),
    )

    op.create_table(
        "user_profile_excluded_foods",
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_user_profile_excluded_foods_food_id_foods"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["user_profiles.id"],
            name=op.f("fk_user_profile_excluded_foods_profile_id_user_profiles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "profile_id", "food_id", name=op.f("pk_user_profile_excluded_foods")
        ),
    )

    # ------------------------------------------------------------ meal plans
    op.create_table(
        "meal_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            _enum("meal_plans", "meal_plan_status", "active", "archived"),
            server_default="active",
            nullable=False,
        ),
        sa.Column("total_calories_kcal", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("total_cost_inr", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_meal_plans_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meal_plans")),
    )
    op.create_index(
        "ix_meal_plans_user_week", "meal_plans", ["user_id", "week_start_date"], unique=False
    )

    op.create_table(
        "planned_meals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meal_plan_id", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("slot", _enum("planned_meals", "meal_slot", *SLOTS), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=True),
        sa.Column("unavailable_reason", sa.Text(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "day_of_week BETWEEN 0 AND 6", name=op.f("ck_planned_meals_day_of_week_range")
        ),
        sa.CheckConstraint(
            "recipe_id IS NOT NULL OR unavailable_reason IS NOT NULL",
            name=op.f("ck_planned_meals_recipe_or_reason"),
        ),
        sa.ForeignKeyConstraint(
            ["meal_plan_id"],
            ["meal_plans.id"],
            name=op.f("fk_planned_meals_meal_plan_id_meal_plans"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_planned_meals_recipe_id_recipes"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_planned_meals")),
        sa.UniqueConstraint(
            "meal_plan_id",
            "day_of_week",
            "slot",
            name=op.f("uq_planned_meals_meal_plan_id_day_of_week_slot"),
        ),
    )
    op.create_index(
        op.f("ix_planned_meals_meal_plan_id"), "planned_meals", ["meal_plan_id"], unique=False
    )
    op.create_index(
        op.f("ix_planned_meals_recipe_id"), "planned_meals", ["recipe_id"], unique=False
    )

    op.create_table(
        "grocery_lists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meal_plan_id", sa.Integer(), nullable=False),
        sa.Column("total_estimated_cost_inr", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["meal_plan_id"],
            ["meal_plans.id"],
            name=op.f("fk_grocery_lists_meal_plan_id_meal_plans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grocery_lists")),
        sa.UniqueConstraint("meal_plan_id", name=op.f("uq_grocery_lists_meal_plan_id")),
    )

    op.create_table(
        "grocery_list_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("grocery_list_id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("unit", _enum("grocery_list_items", "measurement_unit", *UNITS), nullable=False),
        sa.Column("estimated_cost_inr", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_grocery_list_items_quantity_positive")),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_grocery_list_items_food_id_foods"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["grocery_list_id"],
            ["grocery_lists.id"],
            name=op.f("fk_grocery_list_items_grocery_list_id_grocery_lists"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grocery_list_items")),
        sa.UniqueConstraint(
            "grocery_list_id", "food_id", name=op.f("uq_grocery_list_items_grocery_list_id_food_id")
        ),
    )
    op.create_index(
        op.f("ix_grocery_list_items_grocery_list_id"),
        "grocery_list_items",
        ["grocery_list_id"],
        unique=False,
    )

    # -------------------------------------------------------------- feedback
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("planned_meal_id", sa.Integer(), nullable=True),
        sa.Column(
            "feedback_type",
            _enum("feedback", "feedback_type", "favourite", "like", "skip", "dislike"),
            nullable=False,
        ),
        sa.Column("score", sa.SmallInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "score IN (-3, -1, 1, 3)", name=op.f("ck_feedback_score_allowed_values")
        ),
        sa.ForeignKeyConstraint(
            ["planned_meal_id"],
            ["planned_meals.id"],
            name=op.f("fk_feedback_planned_meal_id_planned_meals"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_feedback_recipe_id_recipes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_feedback_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback")),
    )
    op.create_index(
        op.f("ix_feedback_planned_meal_id"), "feedback", ["planned_meal_id"], unique=False
    )
    op.create_index("ix_feedback_user_recipe", "feedback", ["user_id", "recipe_id"], unique=False)

    # -------------------------------------------------------- reference data
    op.bulk_insert(
        meal_categories,
        [
            {"slot": "breakfast", "name": "Breakfast", "display_order": 1},
            {"slot": "lunch", "name": "Lunch", "display_order": 2},
            {"slot": "dinner", "name": "Dinner", "display_order": 3},
            {"slot": "snack", "name": "Snack", "display_order": 4},
        ],
    )
    op.bulk_insert(
        allergens,
        [
            {"name": name}
            for name in (
                "Peanuts",
                "Tree Nuts",
                "Dairy",
                "Egg",
                "Gluten",
                "Soy",
                "Fish",
                "Shellfish",
                "Sesame",
                "Mustard",
            )
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_feedback_user_recipe", table_name="feedback")
    op.drop_index(op.f("ix_feedback_planned_meal_id"), table_name="feedback")
    op.drop_table("feedback")
    op.drop_index(op.f("ix_grocery_list_items_grocery_list_id"), table_name="grocery_list_items")
    op.drop_table("grocery_list_items")
    op.drop_table("grocery_lists")
    op.drop_index(op.f("ix_planned_meals_recipe_id"), table_name="planned_meals")
    op.drop_index(op.f("ix_planned_meals_meal_plan_id"), table_name="planned_meals")
    op.drop_table("planned_meals")
    op.drop_index("ix_meal_plans_user_week", table_name="meal_plans")
    op.drop_table("meal_plans")
    op.drop_table("user_profile_excluded_foods")
    op.drop_table("user_profile_allergens")
    op.drop_table("user_profiles")
    op.drop_table("recipe_nutrition")
    op.drop_index(op.f("ix_recipe_ingredients_recipe_id"), table_name="recipe_ingredients")
    op.drop_index(op.f("ix_recipe_ingredients_food_id"), table_name="recipe_ingredients")
    op.drop_table("recipe_ingredients")
    op.drop_index(op.f("ix_recipes_category_id"), table_name="recipes")
    op.drop_table("recipes")
    op.drop_table("food_nutrition")
    op.drop_table("food_allergens")
    op.drop_table("foods")
    op.drop_table("meal_categories")
    op.drop_table("allergens")
    op.drop_table("users")
