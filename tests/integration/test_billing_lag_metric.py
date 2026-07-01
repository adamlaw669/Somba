"""billing_lag_seconds metric: logs the delay from next_bill_date to the
moment a ChargeAttempt is actually created, so backlog is observable."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from somba.nomba.client import NombaChargeResult, NombaChargeStatus
from somba.workers.charge import worker as charge_worker
from somba.workers.charge.worker import execute_pending, run

UTC = timezone.utc
NOW = datetime(2026, 6, 28, 12, 0, 0, tzinfo=UTC)
DUE_AT = NOW - timedelta(minutes=90)  # subscription became due 90 minutes ago


def _mock_success(**kwargs) -> NombaChargeResult:
    return NombaChargeResult(
        status=NombaChargeStatus.succeeded,
        transaction_id="txn-lag-1",
        failure_reason=None,
        response_code="00",
    )


def test_billing_lag_seconds_logged_on_attempt(
    db, merchant_and_token, make_plan, make_customer, make_subscription, monkeypatch, caplog
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant, amount=10_000)
    customer = make_customer(merchant)
    customer.mandate_id = "mandate_lag_test"
    db.commit()
    sub = make_subscription(
        merchant, customer, plan,
        status=charge_worker.SubscriptionStatus.active,
        next_bill_date=DUE_AT,
        current_period_start=DUE_AT - timedelta(days=30),
        current_period_end=DUE_AT,
    )

    monkeypatch.setattr(charge_worker.nomba_client, "debit_mandate", _mock_success)

    run(db, cutoff=NOW)
    with caplog.at_level(logging.INFO, logger="somba.workers.charge.worker"):
        execute_pending(db, now=NOW)

    lag_lines = [r.message for r in caplog.records if "billing_lag_seconds" in r.message]
    assert len(lag_lines) == 1
    assert f"sub={sub.id}" in lag_lines[0]

    # DUE_AT was 90 minutes (5400s) before NOW.
    assert "lag_seconds=5400.0" in lag_lines[0]


def test_billing_lag_seconds_skipped_when_no_next_bill_date(
    db, merchant_and_token, make_plan, make_customer, make_subscription, monkeypatch, caplog
):
    """No next_bill_date (e.g. a manually-triggered retry) logs nothing, not a crash."""
    from somba.workers.reconcile.writer import write_intent
    from somba.db.models import Invoice, InvoiceStatus, InvoiceType, SubscriptionStatus

    merchant, _ = merchant_and_token
    plan = make_plan(merchant, amount=10_000)
    customer = make_customer(merchant)
    customer.mandate_id = "mandate_lag_test_2"
    db.commit()
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.past_due,
        next_bill_date=None,
    )
    invoice = Invoice(
        merchant_id=merchant.id, subscription_id=sub.id, customer_id=customer.id,
        amount=10_000, status=InvoiceStatus.open, type=InvoiceType.regular,
        period_start=NOW - timedelta(days=30), period_end=NOW,
    )
    db.add(invoice)
    db.flush()
    write_intent(
        db, merchant_id=merchant.id, subscription_id=sub.id, invoice_id=invoice.id,
        order_reference="order-no-due-date", amount=10_000, idempotency_key="idem-no-due-date",
    )
    db.commit()

    monkeypatch.setattr(charge_worker.nomba_client, "debit_mandate", _mock_success)

    with caplog.at_level(logging.INFO, logger="somba.workers.charge.worker"):
        execute_pending(db, now=NOW)

    lag_lines = [r.message for r in caplog.records if "billing_lag_seconds" in r.message]
    assert lag_lines == []
