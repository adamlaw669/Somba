"""Move API keys off the merchant row into a proper api_keys table.

Merchants can now mint several named API keys from the dashboard (e.g. one
per environment) instead of holding a single unnamed key directly on the
merchant record. Existing single keys are carried over as a key named
"Default" before the old columns are dropped.

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_id", sa.String(32), unique=True, nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_api_keys_merchant_id", "api_keys", ["merchant_id"])
    op.create_index("ix_api_keys_key_id", "api_keys", ["key_id"])

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO api_keys (merchant_id, name, key_id, key_hash)
            SELECT id, 'Default', api_key_id, api_key_hash
            FROM merchants
            WHERE api_key_id IS NOT NULL
            """
        )
    )

    with op.batch_alter_table("merchants") as batch_op:
        batch_op.drop_index("ix_merchants_api_key_id")
        batch_op.drop_column("api_key_hash")
        batch_op.drop_column("api_key_id")


def downgrade() -> None:
    with op.batch_alter_table("merchants") as batch_op:
        batch_op.add_column(sa.Column("api_key_id", sa.String(32), nullable=True))
        batch_op.add_column(sa.Column("api_key_hash", sa.String(255), nullable=True))
        batch_op.create_index("ix_merchants_api_key_id", ["api_key_id"])

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE merchants
            SET api_key_id = (
                    SELECT key_id FROM api_keys
                    WHERE api_keys.merchant_id = merchants.id
                    ORDER BY api_keys.created_at ASC LIMIT 1
                ),
                api_key_hash = (
                    SELECT key_hash FROM api_keys
                    WHERE api_keys.merchant_id = merchants.id
                    ORDER BY api_keys.created_at ASC LIMIT 1
                )
            """
        )
    )

    op.drop_index("ix_api_keys_key_id", table_name="api_keys")
    op.drop_index("ix_api_keys_merchant_id", table_name="api_keys")
    op.drop_table("api_keys")
