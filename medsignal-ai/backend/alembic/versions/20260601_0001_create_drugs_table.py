"""create drugs table

Revision ID: 20260601_0001
Revises:
Create Date: 2026-06-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260601_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drugs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rxcui", sa.String(length=64), nullable=True),
        sa.Column("input_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=True),
        sa.Column("synonym", sa.String(length=255), nullable=True),
        sa.Column("tty", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_drugs_id"), "drugs", ["id"], unique=False)
    op.create_index(op.f("ix_drugs_input_name"), "drugs", ["input_name"], unique=False)
    op.create_index(
        op.f("ix_drugs_normalized_name"), "drugs", ["normalized_name"], unique=False
    )
    op.create_index(op.f("ix_drugs_rxcui"), "drugs", ["rxcui"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_drugs_rxcui"), table_name="drugs")
    op.drop_index(op.f("ix_drugs_normalized_name"), table_name="drugs")
    op.drop_index(op.f("ix_drugs_input_name"), table_name="drugs")
    op.drop_index(op.f("ix_drugs_id"), table_name="drugs")
    op.drop_table("drugs")
