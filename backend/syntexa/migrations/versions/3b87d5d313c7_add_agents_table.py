"""add agents table

Revision ID: 3b87d5d313c7
Revises: d46ac74852ca
Create Date: 2026-04-22 14:30:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b87d5d313c7'
down_revision: str | Sequence[str] | None = 'd46ac74852ca'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["provider_id"],
            ["llm_providers.id"],
            name="fk_agents_provider_id_llm_providers",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("agents", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_agents_name"), ["name"], unique=True
        )
        batch_op.create_index(
            batch_op.f("ix_agents_provider_id"), ["provider_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_agents_is_active"), ["is_active"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("agents", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_agents_is_active"))
        batch_op.drop_index(batch_op.f("ix_agents_provider_id"))
        batch_op.drop_index(batch_op.f("ix_agents_name"))
    op.drop_table("agents")
