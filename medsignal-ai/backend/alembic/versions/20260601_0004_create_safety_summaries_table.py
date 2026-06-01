"""create safety summaries table

Revision ID: 20260601_0004
Revises: 20260601_0003
Create Date: 2026-06-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260601_0004"
down_revision: Union[str, None] = "20260601_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "safety_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drug_id", sa.Integer(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("input_length", sa.Integer(), nullable=False),
        sa.Column("output_length", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["drug_id"], ["drugs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_safety_summaries_drug_id"), "safety_summaries", ["drug_id"])
    op.create_index(op.f("ix_safety_summaries_id"), "safety_summaries", ["id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_safety_summaries_id"), table_name="safety_summaries")
    op.drop_index(op.f("ix_safety_summaries_drug_id"), table_name="safety_summaries")
    op.drop_table("safety_summaries")
