"""Partial index on outbox_events pending rows for the relay.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

# The relay's ONLY query is: WHERE status = 'pending' ORDER BY id.
# A partial index over just the unpublished rows stays tiny no matter how
# many millions of published rows pile up — a row drops out of the index
# the moment it's marked published. This replaces the broad status index,
# which indexed every row (including the published ones nobody queries).
_PENDING = sa.text("status = 'pending'")


def upgrade() -> None:
    op.drop_index("ix_outbox_events_status", table_name="outbox_events")
    op.create_index(
        "ix_outbox_events_pending",
        "outbox_events",
        ["id"],
        postgresql_where=_PENDING,
        sqlite_where=_PENDING,
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_events_pending", table_name="outbox_events")
    op.create_index("ix_outbox_events_status", "outbox_events", ["status"])
