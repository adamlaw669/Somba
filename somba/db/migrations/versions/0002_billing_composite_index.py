"""Composite index on subscriptions(status, next_bill_date) for billing sweep.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-28
"""

from __future__ import annotations

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_subscriptions_status_next_bill_date",
        "subscriptions",
        ["status", "next_bill_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_subscriptions_status_next_bill_date", table_name="subscriptions")
