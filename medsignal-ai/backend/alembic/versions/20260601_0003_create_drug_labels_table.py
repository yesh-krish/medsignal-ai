"""create drug labels table

Revision ID: 20260601_0003
Revises: 20260601_0002
Create Date: 2026-06-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260601_0003"
down_revision: Union[str, None] = "20260601_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drug_labels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drug_id", sa.Integer(), nullable=False),
        sa.Column("set_id", sa.String(length=255), nullable=True),
        sa.Column("brand_name", sa.JSON(), nullable=True),
        sa.Column("generic_name", sa.JSON(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=True),
        sa.Column("adverse_reactions", sa.JSON(), nullable=True),
        sa.Column("contraindications", sa.JSON(), nullable=True),
        sa.Column("indications_and_usage", sa.JSON(), nullable=True),
        sa.Column("boxed_warning", sa.JSON(), nullable=True),
        sa.Column("raw_label_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["drug_id"], ["drugs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_drug_labels_drug_id"), "drug_labels", ["drug_id"])
    op.create_index(op.f("ix_drug_labels_id"), "drug_labels", ["id"])
    op.create_index(op.f("ix_drug_labels_set_id"), "drug_labels", ["set_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_drug_labels_set_id"), table_name="drug_labels")
    op.drop_index(op.f("ix_drug_labels_id"), table_name="drug_labels")
    op.drop_index(op.f("ix_drug_labels_drug_id"), table_name="drug_labels")
    op.drop_table("drug_labels")
