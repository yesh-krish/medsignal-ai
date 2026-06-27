"""create medication lists

Revision ID: 20260624_0010
Revises: 20260624_0009
Create Date: 2026-06-24 00:10:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260624_0010"
down_revision: Union[str, None] = "20260624_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "medication_lists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_medication_lists_id"), "medication_lists", ["id"])

    op.create_table(
        "medication_list_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("medication_list_id", sa.Integer(), nullable=False),
        sa.Column("drug_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["drug_id"], ["drugs.id"]),
        sa.ForeignKeyConstraint(["medication_list_id"], ["medication_lists.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("medication_list_id", "drug_id", name="uq_med_list_drug"),
    )
    op.create_index(
        op.f("ix_medication_list_items_drug_id"),
        "medication_list_items",
        ["drug_id"],
    )
    op.create_index(op.f("ix_medication_list_items_id"), "medication_list_items", ["id"])
    op.create_index(
        op.f("ix_medication_list_items_medication_list_id"),
        "medication_list_items",
        ["medication_list_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_medication_list_items_medication_list_id"),
        table_name="medication_list_items",
    )
    op.drop_index(op.f("ix_medication_list_items_id"), table_name="medication_list_items")
    op.drop_index(
        op.f("ix_medication_list_items_drug_id"),
        table_name="medication_list_items",
    )
    op.drop_table("medication_list_items")
    op.drop_index(op.f("ix_medication_lists_id"), table_name="medication_lists")
    op.drop_table("medication_lists")
