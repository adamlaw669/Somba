"""Fix customers schema drift: the ORM model has mandate_id/bank_account_number/
bank_code (added for the direct-debit flow) but 0001 never migrated them in —
it still has the old token_key column instead. Tests never caught this because
they build tables straight from the ORM model, bypassing Alembic entirely.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("mandate_id", sa.String(255), nullable=True))
    op.add_column("customers", sa.Column("bank_account_number", sa.String(32), nullable=True))
    op.add_column("customers", sa.Column("bank_code", sa.String(16), nullable=True))
    op.drop_column("customers", "token_key")


def downgrade() -> None:
    op.add_column("customers", sa.Column("token_key", sa.String(255), nullable=True))
    op.drop_column("customers", "bank_code")
    op.drop_column("customers", "bank_account_number")
    op.drop_column("customers", "mandate_id")
