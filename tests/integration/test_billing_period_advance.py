"""Billing period must advance after a successful regular charge.

Found live: next_bill_date/current_period_start/current_period_end were only
ever set once, at subscription creation. Nothing advanced them after a
successful charge, so a subscription was picked up as "due" again the very
next day -- and the second charge crashed outright on
uq_invoices_subscription_period_start, since _get_or_create_open_invoice
would try to create a second invoice for the exact same period_start.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from somba.db.models import Invoice, LedgerIntent, SubscriptionStatus
from somba.nomba.client import NombaChargeResult, NombaChargeStatus
from somba.workers.charge import worker as charge_worker
from somba.workers.charge.worker import execute_pending
from somba.workers.charge.worker import run as billing_run

UTC = timezone.utc
MONTH_1 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
MONTH_2 = MONTH_1 + timedelta(days=30)


def _mock_success(**kwargs) -> NombaChargeResult:
    return NombaChargeResult(
        status=NombaChargeStatus.succeeded, transaction_id="txn", failure_reason=None, response_code="00",
    )


def _charge(db, now):
    billing_run(db, cutoff=now)
    return execute_pending(db, now=now)


def _naive(dt: datetime) -> datetime:
    """SQLite returns naive datetimes; strip tz from the expected side to compare."""
    return dt.replace(tzinfo=None)


def test_period_advances_after_successful_regular_charge(
    db, merchant_and_token, make_plan, make_customer, make_subscription, monkeypatch
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant, amount=5000, interval="month")
    customer = make_customer(merchant)
    customer.mandate_id = "mandate-period-test"
    db.commit()
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=MONTH_1,
        current_period_start=MONTH_1 - timedelta(days=30),
        current_period_end=MONTH_1,
    )

    monkeypatch.setattr(charge_worker.nomba_client, "debit_mandate", _mock_success)
    processed = _charge(db, MONTH_1)
    assert processed == 1

    db.refresh(sub)
    assert sub.current_period_start == _naive(MONTH_1)
    assert sub.current_period_end == _naive(MONTH_1 + timedelta(days=30))
    assert sub.next_bill_date == _naive(MONTH_1 + timedelta(days=30))


def test_subscription_survives_two_consecutive_billing_cycles(
    db, merchant_and_token, make_plan, make_customer, make_subscription, monkeypatch
):
    """Regression test for the exact production crash: a second real billing
    cycle must succeed, not violate uq_invoices_subscription_period_start."""
    merchant, _ = merchant_and_token
    plan = make_plan(merchant, amount=5000, interval="month")
    customer = make_customer(merchant)
    customer.mandate_id = "mandate-period-test-2"
    db.commit()
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=MONTH_1,
        current_period_start=MONTH_1 - timedelta(days=30),
        current_period_end=MONTH_1,
    )

    monkeypatch.setattr(charge_worker.nomba_client, "debit_mandate", _mock_success)

    processed_1 = _charge(db, MONTH_1)
    assert processed_1 == 1

    # Without the fix this raises IntegrityError on uq_invoices_subscription_period_start
    # because next_bill_date never advanced past MONTH_1.
    processed_2 = _charge(db, MONTH_2)
    assert processed_2 == 1

    invoices = list(db.scalars(select(Invoice).where(Invoice.subscription_id == sub.id)))
    assert len(invoices) == 2
    period_starts = {i.period_start for i in invoices}
    assert len(period_starts) == 2, "two distinct billing periods, not a collision"

    intents = db.scalar(select(func.count()).select_from(LedgerIntent).where(LedgerIntent.subscription_id == sub.id))
    assert intents == 2  # one intent per period, not double-billed within a period

    db.refresh(sub)
    assert sub.next_bill_date == _naive(MONTH_2 + timedelta(days=30))


def test_proration_invoice_success_does_not_advance_period(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    """A mid-cycle top-up charge must not move the subscription's regular period."""
    from somba.db.models import InvoiceStatus, InvoiceType
    from somba.workers.reconcile.writer import write_intent

    merchant, _ = merchant_and_token
    plan = make_plan(merchant, amount=5000, interval="month")
    customer = make_customer(merchant)
    customer.mandate_id = "mandate-period-test-3"
    db.commit()
    period_start = MONTH_1 - timedelta(days=15)
    period_end = MONTH_1 + timedelta(days=15)
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=period_end,
        current_period_start=period_start,
        current_period_end=period_end,
    )

    proration_invoice = Invoice(
        merchant_id=merchant.id, subscription_id=sub.id, customer_id=customer.id,
        amount=3000, status=InvoiceStatus.open, type=InvoiceType.proration,
        period_start=MONTH_1, period_end=period_end, due_date=MONTH_1,
    )
    db.add(proration_invoice)
    db.flush()
    write_intent(
        db, merchant_id=merchant.id, subscription_id=sub.id, invoice_id=proration_invoice.id,
        order_reference="order-prorate-test", amount=3000, idempotency_key="idem-prorate-test",
    )
    db.commit()

    from unittest.mock import patch
    with patch("somba.nomba.client.debit_mandate", side_effect=_mock_success):
        processed = execute_pending(db, now=MONTH_1)
    assert processed == 1

    db.refresh(sub)
    assert sub.current_period_start == _naive(period_start), "proration success must not move the regular period"
    assert sub.current_period_end == _naive(period_end)
    assert sub.next_bill_date == _naive(period_end)
