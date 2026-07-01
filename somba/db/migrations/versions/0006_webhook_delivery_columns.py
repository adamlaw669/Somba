"""Fix webhook_deliveries schema drift: the ORM model has outbox_event_id
(FK, used to look up an existing delivery per event) and last_response_status,
but 0001 never migrated them in. Same root cause as 0005 -- caught by diffing
every table's migration-derived schema against Base.metadata directly, since
tests build tables straight from the ORM model and never exercise Alembic.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch mode: SQLite can't ALTER TABLE ADD COLUMN with an inline FK
    # constraint directly (needs copy-and-move); Postgres runs this as a
    # plain ALTER either way, so batch mode keeps both dialects working.
    with op.batch_alter_table("webhook_deliveries") as batch_op:
        batch_op.add_column(
            sa.Column(
                "outbox_event_id",
                sa.Integer(),
                sa.ForeignKey("outbox_events.id", name="fk_webhook_deliveries_outbox_event_id"),
                nullable=True,
            )
        )
        batch_op.add_column(sa.Column("last_response_status", sa.Integer(), nullable=True))
    op.create_index("ix_webhook_deliveries_outbox_event_id", "webhook_deliveries", ["outbox_event_id"])


def downgrade() -> None:
    op.drop_index("ix_webhook_deliveries_outbox_event_id", table_name="webhook_deliveries")
    with op.batch_alter_table("webhook_deliveries") as batch_op:
        batch_op.drop_column("last_response_status")
        batch_op.drop_column("outbox_event_id")
