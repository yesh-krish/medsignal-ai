"""create safety alerts table

Revision ID: 20260603_0006
Revises: 20260603_0005
Create Date: 2026-06-03 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260603_0006"
down_revision: Union[str, None] = "20260603_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "safety_alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drug_id", sa.Integer(), nullable=False),
        sa.Column("alert_type", sa.String(length=100), nullable=False),
        sa.Column("reaction", sa.String(length=255), nullable=True),
        sa.Column("baseline_count", sa.Integer(), nullable=False),
        sa.Column("current_count", sa.Integer(), nullable=False),
        sa.Column("percent_change", sa.Float(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["drug_id"], ["drugs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_safety_alerts_alert_type"), "safety_alerts", ["alert_type"])
    op.create_index(op.f("ix_safety_alerts_drug_id"), "safety_alerts", ["drug_id"])
    op.create_index(op.f("ix_safety_alerts_id"), "safety_alerts", ["id"])
    op.create_index(op.f("ix_safety_alerts_reaction"), "safety_alerts", ["reaction"])


def downgrade() -> None:
    op.drop_index(op.f("ix_safety_alerts_reaction"), table_name="safety_alerts")
    op.drop_index(op.f("ix_safety_alerts_id"), table_name="safety_alerts")
    op.drop_index(op.f("ix_safety_alerts_drug_id"), table_name="safety_alerts")
    op.drop_index(op.f("ix_safety_alerts_alert_type"), table_name="safety_alerts")
    op.drop_table("safety_alerts")
