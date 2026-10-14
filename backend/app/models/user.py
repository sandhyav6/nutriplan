"""User accounts and nutrition profiles (ER: USER, USER_PROFILE)."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Table,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import (
    ActivityLevel,
    DietaryPreference,
    Gender,
    HealthGoal,
    UserRole,
    enum_column,
)

if TYPE_CHECKING:
    from app.models.catalog import Allergen, Food
    from app.models.feedback import Feedback
    from app.models.meal_plan import MealPlan


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Stored normalised to lower case by the service layer; uniqueness enforced here.
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Salted one-way hash (SRS §5.3); never a plaintext password.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Registration always creates USER; ADMIN is assigned out-of-band, never self-assigned.
    role: Mapped[UserRole] = mapped_column(
        enum_column(UserRole, "user_role"),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.USER.value,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )

    profile: Mapped[UserProfile | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    meal_plans: Mapped[list[MealPlan]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    feedback: Mapped[list[Feedback]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# Declared allergies are structural (SRS REQ-4.2.3): a profile references allergen rows ...
user_profile_allergens = Table(
    "user_profile_allergens",
    Base.metadata,
    Column("profile_id", ForeignKey("user_profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("allergen_id", ForeignKey("allergens.id", ondelete="RESTRICT"), primary_key=True),
)

# ... and may additionally exclude specific foods the user reacts to (e.g. mushrooms).
user_profile_excluded_foods = Table(
    "user_profile_excluded_foods",
    Base.metadata,
    Column("profile_id", ForeignKey("user_profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("food_id", ForeignKey("foods.id", ondelete="CASCADE"), primary_key=True),
)


class UserProfile(TimestampMixin, Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint("age BETWEEN 13 AND 100", name="age_range"),
        CheckConstraint("height_cm BETWEEN 100 AND 250", name="height_range"),
        CheckConstraint("weight_kg BETWEEN 25 AND 300", name="weight_range"),
        CheckConstraint("weekly_budget_inr > 0", name="budget_positive"),
        CheckConstraint("max_cooking_time_min BETWEEN 5 AND 240", name="cooking_time_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    age: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    gender: Mapped[Gender] = mapped_column(enum_column(Gender, "gender"), nullable=False)
    height_cm: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    activity_level: Mapped[ActivityLevel] = mapped_column(
        enum_column(ActivityLevel, "activity_level"), nullable=False
    )
    dietary_preference: Mapped[DietaryPreference] = mapped_column(
        enum_column(DietaryPreference, "dietary_preference"), nullable=False
    )
    health_goal: Mapped[HealthGoal] = mapped_column(
        enum_column(HealthGoal, "health_goal"), nullable=False
    )
    weekly_budget_inr: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_cooking_time_min: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    user: Mapped[User] = relationship(back_populates="profile")
    allergens: Mapped[list[Allergen]] = relationship(secondary=user_profile_allergens)
    excluded_foods: Mapped[list[Food]] = relationship(secondary=user_profile_excluded_foods)
