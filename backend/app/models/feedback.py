"""Feedback events (ER: FEEDBACK). Stored as events with a timestamp (REQ-4.4.2)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, SmallInteger, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import FeedbackType, enum_column

if TYPE_CHECKING:
    from app.models.catalog import Recipe
    from app.models.meal_plan import PlannedMeal
    from app.models.user import User


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (
        Index("ix_feedback_user_recipe", "user_id", "recipe_id"),
        CheckConstraint("score IN (-3, -1, 1, 3)", name="score_allowed_values"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    planned_meal_id: Mapped[int | None] = mapped_column(
        ForeignKey("planned_meals.id", ondelete="SET NULL"), index=True
    )
    feedback_type: Mapped[FeedbackType] = mapped_column(
        enum_column(FeedbackType, "feedback_type"), nullable=False
    )
    # Weighted score recorded at submission time (Favourite +3, Like +1, Skip -1, Dislike -3).
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="feedback")
    recipe: Mapped[Recipe] = relationship()
    planned_meal: Mapped[PlannedMeal | None] = relationship()
