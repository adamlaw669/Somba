"""Initial schema — all tables.

Revision ID: 0001
Revises:
Create Date: 2026-06-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "merchants",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("api_key_id", sa.String(32), unique=True, nullable=False),
        sa.Column("api_key_hash", sa.String(255), nullable=False),
        sa.Column("webhook_url", sa.String(2048), nullable=True),
        sa.Column("webhook_secret", sa.String(255), nullable=False),
    )
    op.create_index("ix_merchants_api_key_id", "merchants", ["api_key_id"])

    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="NGN"),
        sa.Column("interval", sa.String(32), nullable=False),
        sa.Column("interval_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("trial_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
    )
    op.create_index("ix_plans_merchant_id", "plans", ["merchant_id"])

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("token_key", sa.String(255), nullable=True),
        sa.Column("va_id", sa.String(255), nullable=True),
        sa.Column("va_account_no", sa.String(32), nullable=True),
        sa.Column("credit_balance", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.create_index("ix_customers_merchant_id", "customers", ["merchant_id"])

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_bill_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("merchant_id", "id", name="uq_subscriptions_merchant_id_id"),
    )
    op.create_index("ix_subscriptions_merchant_id", "subscriptions", ["merchant_id"])
    op.create_index("ix_subscriptions_customer_id", "subscriptions", ["customer_id"])
    op.create_index("ix_subscriptions_plan_id", "subscriptions", ["plan_id"])
    op.create_index("ix_subscriptions_next_bill_date", "subscriptions", ["next_bill_date"])

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("type", sa.String(32), nullable=False, server_default="regular"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("subscription_id", "period_start", name="uq_invoices_subscription_period_start"),
    )
    op.create_index("ix_invoices_merchant_id", "invoices", ["merchant_id"])
    op.create_index("ix_invoices_subscription_id", "invoices", ["subscription_id"])
    op.create_index("ix_invoices_customer_id", "invoices", ["customer_id"])

    op.create_table(
        "invoice_line_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_invoice_line_items_invoice_id", "invoice_line_items", ["invoice_id"])
    op.create_index("ix_invoice_line_items_merchant_id", "invoice_line_items", ["merchant_id"])

    op.create_table(
        "charge_attempts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(255), unique=True, nullable=False),
        sa.Column("order_reference", sa.String(255), unique=True, nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("failure_reason", sa.String(255), nullable=True),
        sa.Column("failure_class", sa.String(32), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_charge_attempts_merchant_id", "charge_attempts", ["merchant_id"])
    op.create_index("ix_charge_attempts_subscription_id", "charge_attempts", ["subscription_id"])
    op.create_index("ix_charge_attempts_invoice_id", "charge_attempts", ["invoice_id"])

    op.create_table(
        "billing_locks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("billing_period", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.UniqueConstraint("subscription_id", "billing_period", name="uq_billing_locks_subscription_period"),
    )
    op.create_index("ix_billing_locks_subscription_id", "billing_locks", ["subscription_id"])

    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("aggregate_type", sa.String(64), nullable=False),
        sa.Column("aggregate_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("partition_key", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
    )
    op.create_index("ix_outbox_events_merchant_id", "outbox_events", ["merchant_id"])
    op.create_index("ix_outbox_events_status", "outbox_events", ["status"])

    op.create_table(
        "ledger_intents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("charge_attempt_id", sa.Integer(), sa.ForeignKey("charge_attempts.id"), nullable=True),
        sa.Column("idempotency_key", sa.String(255), unique=True, nullable=False),
        sa.Column("order_reference", sa.String(255), unique=True, nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
    )
    op.create_index("ix_ledger_intents_merchant_id", "ledger_intents", ["merchant_id"])
    op.create_index("ix_ledger_intents_subscription_id", "ledger_intents", ["subscription_id"])
    op.create_index("ix_ledger_intents_invoice_id", "ledger_intents", ["invoice_id"])

    op.create_table(
        "ledger_settlements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("intent_id", sa.Integer(), sa.ForeignKey("ledger_intents.id"), nullable=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=True),
        sa.Column("order_reference", sa.String(255), nullable=False),
        sa.Column("transaction_ref", sa.String(255), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_ledger_settlements_merchant_id", "ledger_settlements", ["merchant_id"])
    op.create_index("ix_ledger_settlements_order_reference", "ledger_settlements", ["order_reference"])
    op.create_index("ix_ledger_settlements_transaction_ref", "ledger_settlements", ["transaction_ref"])

    op.create_table(
        "subscription_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("from_status", sa.String(64), nullable=False),
        sa.Column("to_status", sa.String(64), nullable=False),
        sa.Column("trigger", sa.String(32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
    )
    op.create_index("ix_subscription_events_subscription_id", "subscription_events", ["subscription_id"])
    op.create_index("ix_subscription_events_merchant_id", "subscription_events", ["merchant_id"])

    op.create_table(
        "recovery_schedules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("charge_attempt_id", sa.Integer(), sa.ForeignKey("charge_attempts.id"), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason_class", sa.String(32), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="scheduled"),
    )
    op.create_index("ix_recovery_schedules_merchant_id", "recovery_schedules", ["merchant_id"])
    op.create_index("ix_recovery_schedules_subscription_id", "recovery_schedules", ["subscription_id"])
    op.create_index("ix_recovery_schedules_invoice_id", "recovery_schedules", ["invoice_id"])
    op.create_index("ix_recovery_schedules_scheduled_for", "recovery_schedules", ["scheduled_for"])

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_webhook_deliveries_merchant_id", "webhook_deliveries", ["merchant_id"])

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="in_progress"),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.JSON(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("merchant_id", "idempotency_key", "method", "path", name="uq_idempotency_records_lookup"),
    )
    op.create_index("ix_idempotency_records_merchant_id", "idempotency_records", ["merchant_id"])


def downgrade() -> None:
    op.drop_table("idempotency_records")
    op.drop_table("webhook_deliveries")
    op.drop_table("recovery_schedules")
    op.drop_table("subscription_events")
    op.drop_table("ledger_settlements")
    op.drop_table("ledger_intents")
    op.drop_table("outbox_events")
    op.drop_table("billing_locks")
    op.drop_table("charge_attempts")
    op.drop_table("invoice_line_items")
    op.drop_table("invoices")
    op.drop_table("subscriptions")
    op.drop_table("customers")
    op.drop_table("plans")
    op.drop_table("merchants")
