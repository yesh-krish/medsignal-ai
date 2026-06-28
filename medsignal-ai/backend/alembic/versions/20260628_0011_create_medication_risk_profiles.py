"""create medication risk profiles

Revision ID: 20260628_0011
Revises: 20260624_0010
Create Date: 2026-06-28 00:11:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260628_0011"
down_revision: Union[str, None] = "20260624_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "medication_risk_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("medication_list_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["medication_list_id"], ["medication_lists.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("medication_list_id"),
    )
    op.create_index(
        op.f("ix_medication_risk_profiles_id"),
        "medication_risk_profiles",
        ["id"],
    )
    op.create_index(
        op.f("ix_medication_risk_profiles_medication_list_id"),
        "medication_risk_profiles",
        ["medication_list_id"],
    )

    op.create_table(
        "medication_risk_factors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("risk_profile_id", sa.Integer(), nullable=False),
        sa.Column("factor_key", sa.String(length=80), nullable=False),
        sa.Column("is_present", sa.Boolean(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["risk_profile_id"], ["medication_risk_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("risk_profile_id", "factor_key", name="uq_risk_profile_factor"),
    )
    op.create_index(
        op.f("ix_medication_risk_factors_id"),
        "medication_risk_factors",
        ["id"],
    )
    op.create_index(
        op.f("ix_medication_risk_factors_risk_profile_id"),
        "medication_risk_factors",
        ["risk_profile_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_medication_risk_factors_risk_profile_id"),
        table_name="medication_risk_factors",
    )
    op.drop_index(op.f("ix_medication_risk_factors_id"), table_name="medication_risk_factors")
    op.drop_table("medication_risk_factors")
    op.drop_index(
        op.f("ix_medication_risk_profiles_medication_list_id"),
        table_name="medication_risk_profiles",
    )
    op.drop_index(
        op.f("ix_medication_risk_profiles_id"),
        table_name="medication_risk_profiles",
    )
    op.drop_table("medication_risk_profiles")
