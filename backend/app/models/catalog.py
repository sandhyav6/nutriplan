"""Food & recipe catalogue (ER: FOOD, NUTRITION_VALUE, MEAL_CATEGORY, RECIPE, RECIPE_INGREDIENT).

Unit convention: every food has one canonical base unit (g, ml or piece). Nutrition
values are stated per `per_quantity` of that unit (e.g. per 100 g) and the price per
`price_quantity` of that unit (e.g. ₹60 per 1000 g). Recipe ingredient quantities use
the same base unit; the service layer validates this when recipes are written.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import DietType, MealSlot, MeasurementUnit, enum_column


class Allergen(Base):
    """Reference list of allergens (e.g. Peanuts, Dairy). Filtering joins on ids, not strings."""

    __tablename__ = "allergens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))


food_allergens = Table(
    "food_allergens",
    Base.metadata,
    Column("food_id", ForeignKey("foods.id", ondelete="CASCADE"), primary_key=True),
    Column("allergen_id", ForeignKey("allergens.id", ondelete="RESTRICT"), primary_key=True),
)


class Food(TimestampMixin, Base):
    """An ingredient that can be bought and used in recipes."""

    __tablename__ = "foods"
    __table_args__ = (
        CheckConstraint("price_inr >= 0", name="price_non_negative"),
        CheckConstraint("price_quantity > 0", name="price_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    food_group: Mapped[str] = mapped_column(String(50), nullable=False)
    diet_type: Mapped[DietType] = mapped_column(enum_column(DietType, "diet_type"), nullable=False)
    unit: Mapped[MeasurementUnit] = mapped_column(
        enum_column(MeasurementUnit, "measurement_unit"), nullable=False
    )
    price_inr: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    allergens: Mapped[list[Allergen]] = relationship(secondary=food_allergens)
    nutrition: Mapped[FoodNutrition | None] = relationship(
        back_populates="food", uselist=False, cascade="all, delete-orphan"
    )


class FoodNutrition(TimestampMixin, Base):
    """Nutrition Value record for one food (class diagram: NUTRITION VALUE)."""

    __tablename__ = "food_nutrition"
    __table_args__ = (
        CheckConstraint("per_quantity > 0", name="per_quantity_positive"),
        CheckConstraint(
            "calories_kcal >= 0 AND protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0",
            name="macros_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    food_id: Mapped[int] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    per_quantity: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    calories_kcal: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    protein_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    carbs_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    fat_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    fibre_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    sodium_mg: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    cholesterol_mg: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))

    food: Mapped[Food] = relationship(back_populates="nutrition")


class MealCategory(Base):
    """One of the four fixed categories. Admins may edit name/description, not add or delete."""

    __tablename__ = "meal_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot: Mapped[MealSlot] = mapped_column(
        enum_column(MealSlot, "meal_slot"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    recipes: Mapped[list[Recipe]] = relationship(back_populates="category")


class Recipe(TimestampMixin, Base):
    __tablename__ = "recipes"
    __table_args__ = (
        CheckConstraint("prep_time_min > 0", name="prep_time_positive"),
        CheckConstraint("servings > 0", name="servings_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Every recipe belongs to exactly one meal category (SRS §2.5, §5.5).
    category_id: Mapped[int] = mapped_column(
        ForeignKey("meal_categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    prep_time_min: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    servings: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, server_default="1"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )

    category: Mapped[MealCategory] = relationship(back_populates="recipes")
    ingredients: Mapped[list[RecipeIngredient]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )
    nutrition: Mapped[RecipeNutrition | None] = relationship(
        back_populates="recipe", uselist=False, cascade="all, delete-orphan"
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        UniqueConstraint("recipe_id", "food_id"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    food_id: Mapped[int] = mapped_column(
        ForeignKey("foods.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[MeasurementUnit] = mapped_column(
        enum_column(MeasurementUnit, "measurement_unit"), nullable=False
    )

    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
    food: Mapped[Food] = relationship()


class RecipeNutrition(Base):
    """Pre-calculated per-serving nutrition and cost (SRS §2.7: values exist before generation)."""

    __tablename__ = "recipe_nutrition"
    __table_args__ = (
        CheckConstraint(
            "calories_kcal >= 0 AND protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0",
            name="macros_non_negative",
        ),
        CheckConstraint("estimated_cost_inr >= 0", name="cost_non_negative"),
    )

    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True
    )
    calories_kcal: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    protein_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    carbs_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    fat_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    fibre_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    estimated_cost_inr: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    recipe: Mapped[Recipe] = relationship(back_populates="nutrition")
