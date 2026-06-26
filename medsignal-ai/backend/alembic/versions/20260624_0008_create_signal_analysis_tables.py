"""create signal analysis tables

Revision ID: 20260624_0008
Revises: 20260624_0007
Create Date: 2026-06-24 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260624_0008"
down_revision: Union[str, None] = "20260624_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "signal_analysis_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drug_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("comparator_scope", sa.String(length=255), nullable=False),
        sa.Column("minimum_reports", sa.Integer(), nullable=False),
        sa.Column("prr_threshold", sa.Float(), nullable=False),
        sa.Column("ror_ci_lower_threshold", sa.Float(), nullable=False),
        sa.Column("target_total_reports", sa.Integer(), nullable=False),
        sa.Column("comparator_total_reports", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["drug_id"], ["drugs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_signal_analysis_runs_drug_id"),
        "signal_analysis_runs",
        ["drug_id"],
    )
    op.create_index(
        op.f("ix_signal_analysis_runs_id"), "signal_analysis_runs", ["id"]
    )
    op.create_index(
        op.f("ix_signal_analysis_runs_status"), "signal_analysis_runs", ["status"]
    )

    op.create_table(
        "signal_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("drug_id", sa.Integer(), nullable=False),
        sa.Column("reaction", sa.String(length=255), nullable=False),
        sa.Column("target_with_reaction", sa.Integer(), nullable=False),
        sa.Column("target_without_reaction", sa.Integer(), nullable=False),
        sa.Column("comparator_with_reaction", sa.Integer(), nullable=False),
        sa.Column("comparator_without_reaction", sa.Integer(), nullable=False),
        sa.Column("prr", sa.Float(), nullable=False),
        sa.Column("ror", sa.Float(), nullable=False),
        sa.Column("ror_ci_lower", sa.Float(), nullable=False),
        sa.Column("ror_ci_upper", sa.Float(), nullable=False),
        sa.Column("is_potential_signal", sa.Boolean(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["drug_id"], ["drugs.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["signal_analysis_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_signal_results_drug_id"), "signal_results", ["drug_id"])
    op.create_index(op.f("ix_signal_results_id"), "signal_results", ["id"])
    op.create_index(
        op.f("ix_signal_results_is_potential_signal"),
        "signal_results",
        ["is_potential_signal"],
    )
    op.create_index(op.f("ix_signal_results_reaction"), "signal_results", ["reaction"])
    op.create_index(op.f("ix_signal_results_run_id"), "signal_results", ["run_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_signal_results_run_id"), table_name="signal_results")
    op.drop_index(op.f("ix_signal_results_reaction"), table_name="signal_results")
    op.drop_index(
        op.f("ix_signal_results_is_potential_signal"), table_name="signal_results"
    )
    op.drop_index(op.f("ix_signal_results_id"), table_name="signal_results")
    op.drop_index(op.f("ix_signal_results_drug_id"), table_name="signal_results")
    op.drop_table("signal_results")

    op.drop_index(
        op.f("ix_signal_analysis_runs_status"), table_name="signal_analysis_runs"
    )
    op.drop_index(
        op.f("ix_signal_analysis_runs_id"), table_name="signal_analysis_runs"
    )
    op.drop_index(
        op.f("ix_signal_analysis_runs_drug_id"), table_name="signal_analysis_runs"
    )
    op.drop_table("signal_analysis_runs")
