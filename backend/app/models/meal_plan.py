"""Weekly plans, planned meals and grocery lists (ER: WEEKLY_PLAN, PLAN_ITEM, GROCERY_LIST)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import MealPlanStatus, MealSlot, MeasurementUnit, enum_column

if TYPE_CHECKING:
    from app.models.catalog import Food, Recipe
    from app.models.user import User


class MealPlan(TimestampMixin, Base):
    __tablename__ = "meal_plans"
    __table_args__ = (Index("ix_meal_plans_user_week", "user_id", "week_start_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[MealPlanStatus] = mapped_column(
        enum_column(MealPlanStatus, "meal_plan_status"),
        nullable=False,
        default=MealPlanStatus.ACTIVE,
        server_default=MealPlanStatus.ACTIVE.value,
    )
    total_calories_kcal: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    total_cost_inr: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    # Explanations returned when constraints could not all be satisfied (SRS §4.2.2).
    notes: Mapped[str | None] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="meal_plans")
    planned_meals: Mapped[list[PlannedMeal]] = relationship(
        back_populates="meal_plan", cascade="all, delete-orphan"
    )
    grocery_list: Mapped[GroceryList | None] = relationship(
        back_populates="meal_plan", uselist=False, cascade="all, delete-orphan"
    )


class PlannedMeal(TimestampMixin, Base):
    """One slot of a weekly plan. A slot with no safe recipe stores an explanation instead."""

    __tablename__ = "planned_meals"
    __table_args__ = (
        UniqueConstraint("meal_plan_id", "day_of_week", "slot"),
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="day_of_week_range"),
        CheckConstraint(
            "recipe_id IS NOT NULL OR unavailable_reason IS NOT NULL",
            name="recipe_or_reason",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meal_plan_id: Mapped[int] = mapped_column(
        ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 0 = Monday
    slot: Mapped[MealSlot] = mapped_column(enum_column(MealSlot, "meal_slot"), nullable=False)
    recipe_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipes.id", ondelete="RESTRICT"), index=True
    )
    unavailable_reason: Mapped[str | None] = mapped_column(Text)  # REQ-4.2.8

    meal_plan: Mapped[MealPlan] = relationship(back_populates="planned_meals")
    recipe: Mapped[Recipe | None] = relationship()


class GroceryList(Base):
    __tablename__ = "grocery_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meal_plan_id: Mapped[int] = mapped_column(
        ForeignKey("meal_plans.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    total_estimated_cost_inr: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    meal_plan: Mapped[MealPlan] = relationship(back_populates="grocery_list")
    items: Mapped[list[GroceryListItem]] = relationship(
        back_populates="grocery_list", cascade="all, delete-orphan"
    )


class GroceryListItem(Base):
    """One aggregated, de-duplicated ingredient line (REQ-4.3.1, REQ-4.3.2)."""

    __tablename__ = "grocery_list_items"
    __table_args__ = (
        UniqueConstraint("grocery_list_id", "food_id"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grocery_list_id: Mapped[int] = mapped_column(
        ForeignKey("grocery_lists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    food_id: Mapped[int] = mapped_column(
        ForeignKey("foods.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit: Mapped[MeasurementUnit] = mapped_column(
        enum_column(MeasurementUnit, "measurement_unit"), nullable=False
    )
    estimated_cost_inr: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    grocery_list: Mapped[GroceryList] = relationship(back_populates="items")
    food: Mapped[Food] = relationship()
