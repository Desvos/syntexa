"""add swarms and swarm_agents tables

Revision ID: 171d57f353b4
Revises: 3a0397047483
Create Date: 2026-04-22 18:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '171d57f353b4'
down_revision: str | Sequence[str] | None = '3a0397047483'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "swarms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("task_description", sa.Text(), nullable=True),
        sa.Column(
            "orchestrator_strategy",
            sa.String(length=16),
            nullable=False,
            server_default="auto",
        ),
        sa.Column("manual_agent_order", sa.Text(), nullable=True),
        sa.Column(
            "max_rounds", sa.Integer(), nullable=False, server_default="60"
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="idle",
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            name="fk_swarms_repository_id_repositories",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("swarms", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_swarms_name"), ["name"], unique=True
        )
        batch_op.create_index(
            batch_op.f("ix_swarms_repository_id"),
            ["repository_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_swarms_status"), ["status"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_swarms_is_active"), ["is_active"], unique=False
        )

    op.create_table(
        "swarm_agents",
        sa.Column("swarm_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column(
            "position", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.ForeignKeyConstraint(
            ["swarm_id"],
            ["swarms.id"],
            name="fk_swarm_agents_swarm_id_swarms",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_swarm_agents_agent_id_agents",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("swarm_id", "agent_id"),
    )


def downgrade() -> None:
    op.drop_table("swarm_agents")
    with op.batch_alter_table("swarms", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_swarms_is_active"))
        batch_op.drop_index(batch_op.f("ix_swarms_status"))
        batch_op.drop_index(batch_op.f("ix_swarms_repository_id"))
        batch_op.drop_index(batch_op.f("ix_swarms_name"))
    op.drop_table("swarms")
