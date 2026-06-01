"""create adverse events table

Revision ID: 20260601_0002
Revises: 20260601_0001
Create Date: 2026-06-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260601_0002"
down_revision: Union[str, None] = "20260601_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "adverse_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drug_id", sa.Integer(), nullable=False),
        sa.Column("reaction", sa.String(length=255), nullable=True),
        sa.Column("serious", sa.Boolean(), nullable=False),
        sa.Column("outcome", sa.String(length=255), nullable=True),
        sa.Column("report_date", sa.Date(), nullable=True),
        sa.Column("patient_age", sa.Float(), nullable=True),
        sa.Column("patient_sex", sa.String(length=32), nullable=True),
        sa.Column("raw_event_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["drug_id"], ["drugs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_adverse_events_drug_id"), "adverse_events", ["drug_id"])
    op.create_index(op.f("ix_adverse_events_id"), "adverse_events", ["id"])
    op.create_index(
        op.f("ix_adverse_events_patient_sex"), "adverse_events", ["patient_sex"]
    )
    op.create_index(
        op.f("ix_adverse_events_reaction"), "adverse_events", ["reaction"]
    )
    op.create_index(
        op.f("ix_adverse_events_report_date"), "adverse_events", ["report_date"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_adverse_events_report_date"), table_name="adverse_events")
    op.drop_index(op.f("ix_adverse_events_reaction"), table_name="adverse_events")
    op.drop_index(op.f("ix_adverse_events_patient_sex"), table_name="adverse_events")
    op.drop_index(op.f("ix_adverse_events_id"), table_name="adverse_events")
    op.drop_index(op.f("ix_adverse_events_drug_id"), table_name="adverse_events")
    op.drop_table("adverse_events")
