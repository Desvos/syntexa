"""drop legacy agent_roles, swarm_compositions, swarm_instances tables

Phase 8 cleanup: these tables were superseded by the first-class Agent,
Swarm, and SwarmAgent entities introduced in Phases 3-5. No data is
migrated — these legacy rows had no consumers after Phase 7.

Revision ID: 9c4f2a8e7b13
Revises: 8b2e9a37c1d4
Create Date: 2026-04-22 22:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '9c4f2a8e7b13'
down_revision: str | Sequence[str] | None = '8b2e9a37c1d4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    # Drop in safe order (no FKs between them, but guard idempotently so
    # fresh installs that never had the legacy tables don't fail).
    for table in ("swarm_instances", "swarm_compositions", "agent_roles"):
        if insp.has_table(table):
            op.drop_table(table)


def downgrade() -> None:
    # Recreate the legacy tables in roughly their last-known shape. No data
    # is restored — downgrade is for schema symmetry only.
    op.create_table(
        "agent_roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("handoff_targets", sa.Text(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    with op.batch_alter_table("agent_roles", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_agent_roles_name"), ["name"], unique=False
        )

    op.create_table(
        "swarm_compositions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("roles", sa.Text(), nullable=False),
        sa.Column("max_rounds", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_type"),
    )
    with op.batch_alter_table("swarm_compositions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_swarm_compositions_task_type"),
            ["task_type"],
            unique=False,
        )

    op.create_table(
        "swarm_instances",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.String(length=32), nullable=False),
        sa.Column("task_name", sa.String(length=256), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("branch", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("active_agent", sa.String(length=64), nullable=True),
        sa.Column("conversation_log", sa.Text(), nullable=True),
        sa.Column("pr_url", sa.String(length=512), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    with op.batch_alter_table("swarm_instances", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_swarm_instances_task_id"), ["task_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_swarm_instances_status"), ["status"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_swarm_instances_completed_at"),
            ["completed_at"],
            unique=False,
        )
        batch_op.create_index(
            "ix_swarm_instances_status_completed",
            ["status", "completed_at"],
            unique=False,
        )
