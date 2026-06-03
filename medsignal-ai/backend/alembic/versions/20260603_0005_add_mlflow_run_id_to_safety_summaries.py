"""add mlflow run id to safety summaries

Revision ID: 20260603_0005
Revises: 20260601_0004
Create Date: 2026-06-03 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260603_0005"
down_revision: Union[str, None] = "20260601_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "safety_summaries",
        sa.Column("mlflow_run_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        op.f("ix_safety_summaries_mlflow_run_id"),
        "safety_summaries",
        ["mlflow_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_safety_summaries_mlflow_run_id"), table_name="safety_summaries"
    )
    op.drop_column("safety_summaries", "mlflow_run_id")
