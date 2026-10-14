from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.models import Base
from app.models.enums import MealSlot

EXPECTED_TABLES = {
    "users",
    "user_profiles",
    "user_profile_allergens",
    "user_profile_excluded_foods",
    "allergens",
    "foods",
    "food_allergens",
    "food_nutrition",
    "meal_categories",
    "recipes",
    "recipe_ingredients",
    "recipe_nutrition",
    "meal_plans",
    "planned_meals",
    "grocery_lists",
    "grocery_list_items",
    "feedback",
    "user_sessions",
}


def test_metadata_contains_core_tables() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_every_table_compiles_for_postgresql() -> None:
    dialect = postgresql.dialect()
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=dialect))
        assert f"CREATE TABLE {table.name}" in ddl


def test_user_email_is_unique() -> None:
    assert Base.metadata.tables["users"].c.email.unique is True


def test_recipe_requires_exactly_one_category() -> None:
    category_id = Base.metadata.tables["recipes"].c.category_id
    assert category_id.nullable is False
    assert {fk.column.table.name for fk in category_id.foreign_keys} == {"meal_categories"}


def test_four_fixed_meal_slots() -> None:
    assert [slot.value for slot in MealSlot] == ["breakfast", "lunch", "dinner", "snack"]


def test_money_columns_use_exact_numeric() -> None:
    money = [
        ("foods", "price_inr"),
        ("user_profiles", "weekly_budget_inr"),
        ("recipe_nutrition", "estimated_cost_inr"),
        ("meal_plans", "total_cost_inr"),
        ("grocery_list_items", "estimated_cost_inr"),
    ]
    for table, column in money:
        col_type = Base.metadata.tables[table].c[column].type
        assert col_type.__class__.__name__ == "Numeric", f"{table}.{column}"
        assert col_type.scale == 2


def test_allergies_are_structural_relationships() -> None:
    profile_allergens = Base.metadata.tables["user_profile_allergens"]
    targets = {fk.column.table.name for fk in profile_allergens.foreign_keys}
    assert targets == {"user_profiles", "allergens"}


def test_constraint_names_follow_convention() -> None:
    users = Base.metadata.tables["users"]
    names = {c.name for c in users.constraints}
    assert "pk_users" in names
    assert "uq_users_email" in names
