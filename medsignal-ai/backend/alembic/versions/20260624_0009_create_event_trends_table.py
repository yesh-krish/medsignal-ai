"""create event trends table

Revision ID: 20260624_0009
Revises: 20260624_0008
Create Date: 2026-06-24 00:09:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260624_0009"
down_revision: Union[str, None] = "20260624_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_trends",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drug_id", sa.Integer(), nullable=False),
        sa.Column("trends_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["drug_id"], ["drugs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("drug_id"),
    )
    op.create_index(op.f("ix_event_trends_drug_id"), "event_trends", ["drug_id"])
    op.create_index(op.f("ix_event_trends_id"), "event_trends", ["id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_event_trends_id"), table_name="event_trends")
    op.drop_index(op.f("ix_event_trends_drug_id"), table_name="event_trends")
    op.drop_table("event_trends")
