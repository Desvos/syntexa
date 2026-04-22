"""add processed_events table and repositories.clickup_trigger_tag

Revision ID: 8b2e9a37c1d4
Revises: 171d57f353b4
Create Date: 2026-04-22 20:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b2e9a37c1d4'
down_revision: str | Sequence[str] | None = '171d57f353b4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add clickup_trigger_tag column to repositories
    with op.batch_alter_table("repositories", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "clickup_trigger_tag", sa.String(length=64), nullable=True
            )
        )

    # 2. Create processed_events dedup table
    op.create_table(
        "processed_events",
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column(
            "processed_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column("swarm_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["swarm_id"],
            ["swarms.id"],
            name="fk_processed_events_swarm_id_swarms",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("source", "external_id"),
    )


def downgrade() -> None:
    op.drop_table("processed_events")
    with op.batch_alter_table("repositories", schema=None) as batch_op:
        batch_op.drop_column("clickup_trigger_tag")
