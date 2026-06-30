"""Add created_at to ledger_intents (for the pending-intent age alert).

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable so SQLite's ADD COLUMN accepts it; the ORM stamps new rows.
    op.add_column(
        "ledger_intents",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ledger_intents", "created_at")
