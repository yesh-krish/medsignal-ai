"""add ingestion provenance

Revision ID: 20260624_0007
Revises: 20260603_0006
Create Date: 2026-06-24 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260624_0007"
down_revision: Union[str, None] = "20260603_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drug_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("requested_reports", sa.Integer(), nullable=False),
        sa.Column("fetched_reports", sa.Integer(), nullable=False),
        sa.Column("saved_reaction_rows", sa.Integer(), nullable=False),
        sa.Column("duplicate_reports_skipped", sa.Integer(), nullable=False),
        sa.Column("source_last_updated", sa.String(length=32), nullable=True),
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
    op.create_index(op.f("ix_ingestion_runs_drug_id"), "ingestion_runs", ["drug_id"])
    op.create_index(op.f("ix_ingestion_runs_id"), "ingestion_runs", ["id"])
    op.create_index(op.f("ix_ingestion_runs_status"), "ingestion_runs", ["status"])

    op.add_column(
        "adverse_events", sa.Column("ingestion_run_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "adverse_events", sa.Column("safety_report_id", sa.String(100), nullable=True)
    )
    op.add_column(
        "adverse_events", sa.Column("case_version", sa.Integer(), nullable=True)
    )
    op.add_column(
        "adverse_events", sa.Column("reaction_index", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_adverse_events_ingestion_run_id",
        "adverse_events",
        "ingestion_runs",
        ["ingestion_run_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_adverse_events_ingestion_run_id"),
        "adverse_events",
        ["ingestion_run_id"],
    )
    op.create_index(
        op.f("ix_adverse_events_safety_report_id"),
        "adverse_events",
        ["safety_report_id"],
    )
    op.create_unique_constraint(
        "uq_adverse_event_report_reaction",
        "adverse_events",
        ["drug_id", "safety_report_id", "case_version", "reaction_index"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_adverse_event_report_reaction", "adverse_events", type_="unique"
    )
    op.drop_index(
        op.f("ix_adverse_events_safety_report_id"), table_name="adverse_events"
    )
    op.drop_index(
        op.f("ix_adverse_events_ingestion_run_id"), table_name="adverse_events"
    )
    op.drop_constraint(
        "fk_adverse_events_ingestion_run_id", "adverse_events", type_="foreignkey"
    )
    op.drop_column("adverse_events", "reaction_index")
    op.drop_column("adverse_events", "case_version")
    op.drop_column("adverse_events", "safety_report_id")
    op.drop_column("adverse_events", "ingestion_run_id")

    op.drop_index(op.f("ix_ingestion_runs_status"), table_name="ingestion_runs")
    op.drop_index(op.f("ix_ingestion_runs_id"), table_name="ingestion_runs")
    op.drop_index(op.f("ix_ingestion_runs_drug_id"), table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
