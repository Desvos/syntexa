"""add llm_providers table

Revision ID: d46ac74852ca
Revises: f544d974925d
Create Date: 2026-04-22 14:06:23.748413

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd46ac74852ca'
down_revision: str | Sequence[str] | None = 'f544d974925d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "llm_providers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("provider_type", sa.String(length=32), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("default_model", sa.String(length=128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("llm_providers", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_llm_providers_name"), ["name"], unique=True
        )
        batch_op.create_index(
            batch_op.f("ix_llm_providers_provider_type"),
            ["provider_type"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_llm_providers_is_active"), ["is_active"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("llm_providers", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_llm_providers_is_active"))
        batch_op.drop_index(batch_op.f("ix_llm_providers_provider_type"))
        batch_op.drop_index(batch_op.f("ix_llm_providers_name"))
    op.drop_table("llm_providers")
