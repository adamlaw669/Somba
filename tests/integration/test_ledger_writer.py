"""Integration tests for the ledger writer: intent writer, settlement writer, matcher."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from somba.db.models import (
    ChargeAttemptStatus,
    Customer,
    Invoice,
    InvoiceStatus,
    LedgerIntent,
    LedgerIntentStatus,
    LedgerSettlement,
    LedgerSettlementSource,
    LedgerSettlementStatus,
    OutboxEvent,
    SubscriptionStatus,
)
from somba.workers.reconcile.writer import write_intent, write_settlement

UTC = timezone.utc
NOW = datetime(2026, 6, 30, 10, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Intent writer
# ---------------------------------------------------------------------------


def test_write_intent_creates_pending_intent(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)

    intent = write_intent(
        db,
        merchant_id=merchant.id,
        subscription_id=sub.id,
        invoice_id=1,
        order_reference="order-abc123",
        amount=10_000,
        idempotency_key="idem-001",
    )
    db.flush()

    assert intent.status == LedgerIntentStatus.pending
    assert intent.order_reference == "order-abc123"
    assert intent.amount == 10_000


def test_write_intent_is_idempotent(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)

    intent1 = write_intent(
        db, merchant_id=merchant.id, subscription_id=sub.id, invoice_id=1,
        order_reference="order-x", amount=5_000, idempotency_key="idem-x",
    )
    db.commit()
    intent2 = write_intent(
        db, merchant_id=merchant.id, subscription_id=sub.id, invoice_id=1,
        order_reference="order-x", amount=5_000, idempotency_key="idem-x",
    )
    assert intent1.id == intent2.id
    assert db.query(LedgerIntent).count() == 1


# ---------------------------------------------------------------------------
# Settlement writer + matcher: matched
# ---------------------------------------------------------------------------


def test_write_settlement_matched_marks_intent_and_heals(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant, amount=10_000)
    customer = make_customer(merchant)
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.past_due,
    )
    invoice = Invoice(
        merchant_id=merchant.id, subscription_id=sub.id, customer_id=customer.id,
        amount=10_000, status=InvoiceStatus.open, period_start=NOW - timedelta(days=30),
        period_end=NOW,
    )
    db.add(invoice)
    db.flush()

    intent = write_intent(
        db, merchant_id=merchant.id, subscription_id=sub.id, invoice_id=invoice.id,
        order_reference="order-heal-01", amount=10_000, idempotency_key="idem-heal-01",
    )
    db.commit()

    res = write_settlement(
        db,
        merchant_id=merchant.id,
        order_reference="order-heal-01",
        transaction_ref="tx-nomba-001",
        amount_kobo=10_000,
        source=LedgerSettlementSource.webhook,
        raw_payload={},
        now=NOW,
    )
    db.commit()

    assert res.status == LedgerSettlementStatus.matched
    assert res.healed is True

    db.refresh(invoice)
    assert invoice.status == InvoiceStatus.paid

    db.refresh(sub)
    assert sub.status == SubscriptionStatus.active

    db.refresh(intent)
    assert intent.status == LedgerIntentStatus.matched


# ---------------------------------------------------------------------------
# Settlement writer + matcher: orphan
# ---------------------------------------------------------------------------


def test_write_settlement_orphan_when_no_matching_intent(
    db, merchant_and_token
):
    merchant, _ = merchant_and_token

    res = write_settlement(
        db,
        merchant_id=merchant.id,
        order_reference="order-unknown",
        transaction_ref="tx-orphan-001",
        amount_kobo=5_000,
        source=LedgerSettlementSource.webhook,
        raw_payload={},
        now=NOW,
    )
    db.flush()

    assert res.status == LedgerSettlementStatus.orphan
    assert res.healed is False
    assert res.intent is None


def test_write_settlement_orphan_va_heals_open_invoice(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    """VA transfer with no matching intent heals via virtual account number."""
    merchant, _ = merchant_and_token
    plan = make_plan(merchant, amount=8_000)
    customer = make_customer(merchant)
    customer.va_account_no = "0123456789"
    db.flush()

    sub = make_subscription(merchant, customer, plan, status=SubscriptionStatus.past_due)
    invoice = Invoice(
        merchant_id=merchant.id, subscription_id=sub.id, customer_id=customer.id,
        amount=8_000, status=InvoiceStatus.open, period_start=NOW - timedelta(days=30),
        period_end=NOW,
    )
    db.add(invoice)
    db.commit()

    payload = {
        "data": {
            "transaction": {
                "destinationAccountNumber": "0123456789",
                "transactionId": "tx-va-heal-001",
                "transactionAmount": 80.0,
            }
        }
    }

    res = write_settlement(
        db,
        merchant_id=merchant.id,
        order_reference="",
        transaction_ref="tx-va-heal-001",
        amount_kobo=8_000,
        source=LedgerSettlementSource.transfer_push,
        raw_payload=payload,
        now=NOW,
    )
    db.commit()

    assert res.healed is True
    db.refresh(invoice)
    assert invoice.status == InvoiceStatus.paid
    db.refresh(sub)
    assert sub.status == SubscriptionStatus.active


# ---------------------------------------------------------------------------
# Settlement writer + matcher: duplicate
# ---------------------------------------------------------------------------


def test_write_settlement_duplicate_same_transaction_ref(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)

    write_intent(
        db, merchant_id=merchant.id, subscription_id=sub.id, invoice_id=1,
        order_reference="order-dup-01", amount=5_000, idempotency_key="idem-dup-01",
    )
    db.commit()

    write_settlement(
        db, merchant_id=merchant.id, order_reference="order-dup-01",
        transaction_ref="tx-dup-001", amount_kobo=5_000,
        source=LedgerSettlementSource.webhook, raw_payload={}, now=NOW,
    )
    db.commit()

    res = write_settlement(
        db, merchant_id=merchant.id, order_reference="order-dup-01",
        transaction_ref="tx-dup-001", amount_kobo=5_000,
        source=LedgerSettlementSource.webhook, raw_payload={}, now=NOW,
    )
    db.commit()

    assert res.status == LedgerSettlementStatus.duplicate
    assert db.query(LedgerSettlement).count() == 1


# ---------------------------------------------------------------------------
# Settlement writer + matcher: anomaly (drift)
# ---------------------------------------------------------------------------


def test_write_settlement_anomaly_on_amount_mismatch(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant, amount=10_000)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)

    write_intent(
        db, merchant_id=merchant.id, subscription_id=sub.id, invoice_id=1,
        order_reference="order-drift-01", amount=10_000, idempotency_key="idem-drift-01",
    )
    db.commit()

    res = write_settlement(
        db, merchant_id=merchant.id, order_reference="order-drift-01",
        transaction_ref="tx-drift-001",
        amount_kobo=9_999,  # 1 kobo short
        source=LedgerSettlementSource.webhook, raw_payload={}, now=NOW,
    )
    db.commit()

    assert res.status == LedgerSettlementStatus.anomaly
    assert res.healed is False
