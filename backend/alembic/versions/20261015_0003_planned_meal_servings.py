"""Portion size for planned meals (OD-21).

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("planned_meals") as batch:
        batch.add_column(
            sa.Column(
                "servings", sa.Numeric(precision=4, scale=2), server_default="1.00", nullable=False
            )
        )
        batch.create_check_constraint(op.f("ck_planned_meals_servings_positive"), "servings > 0")


def downgrade() -> None:
    with op.batch_alter_table("planned_meals") as batch:
        batch.drop_constraint(op.f("ck_planned_meals_servings_positive"), type_="check")
        batch.drop_column("servings")
