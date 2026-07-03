"""Add dashboard email/password auth, separate from the API key credential.

Merchants now sign up with name/email/password and mint an API key later from
the dashboard, instead of getting one immediately at account creation. Adds
merchants.email/password_hash, makes api_key_id/api_key_hash nullable (no key
until minted), and adds merchant_sessions for dashboard login sessions.

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("merchants") as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("password_hash", sa.String(255), nullable=True))
        batch_op.alter_column("api_key_id", existing_type=sa.String(32), nullable=True)
        batch_op.alter_column("api_key_hash", existing_type=sa.String(255), nullable=True)
        batch_op.alter_column(
            "webhook_secret", existing_type=sa.String(255), nullable=False, server_default=""
        )
    op.create_index("ix_merchants_email", "merchants", ["email"], unique=True)

    op.create_table(
        "merchant_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("session_id", sa.String(32), unique=True, nullable=False),
        sa.Column("session_secret_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_merchant_sessions_merchant_id", "merchant_sessions", ["merchant_id"])
    op.create_index("ix_merchant_sessions_session_id", "merchant_sessions", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_merchant_sessions_session_id", table_name="merchant_sessions")
    op.drop_index("ix_merchant_sessions_merchant_id", table_name="merchant_sessions")
    op.drop_table("merchant_sessions")

    op.drop_index("ix_merchants_email", table_name="merchants")
    with op.batch_alter_table("merchants") as batch_op:
        batch_op.alter_column("webhook_secret", existing_type=sa.String(255), nullable=False)
        batch_op.alter_column("api_key_hash", existing_type=sa.String(255), nullable=False)
        batch_op.alter_column("api_key_id", existing_type=sa.String(32), nullable=False)
        batch_op.drop_column("password_hash")
        batch_op.drop_column("email")
