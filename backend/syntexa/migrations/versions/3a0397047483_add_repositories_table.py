"""add repositories table

Revision ID: 3a0397047483
Revises: 3b87d5d313c7
Create Date: 2026-04-22 16:31:27.189771

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a0397047483'
down_revision: str | Sequence[str] | None = '3b87d5d313c7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("remote_url", sa.String(length=512), nullable=True),
        sa.Column(
            "default_branch",
            sa.String(length=128),
            nullable=False,
            server_default="main",
        ),
        sa.Column("clickup_list_id", sa.String(length=64), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("repositories", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_repositories_name"), ["name"], unique=True
        )
        batch_op.create_index(
            batch_op.f("ix_repositories_path"), ["path"], unique=True
        )
        batch_op.create_index(
            batch_op.f("ix_repositories_is_active"), ["is_active"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("repositories", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_repositories_is_active"))
        batch_op.drop_index(batch_op.f("ix_repositories_path"))
        batch_op.drop_index(batch_op.f("ix_repositories_name"))
    op.drop_table("repositories")
