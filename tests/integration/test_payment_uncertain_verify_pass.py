"""Integration test: payment_uncertain -> verify pass -> active.

A charge attempt that comes back "uncertain" (e.g. a Nomba timeout) must not
be silently lost or double-charged: it parks the subscription in
payment_uncertain and leaves the intent pending. The verify pass later asks
Nomba for the definitive status and, on confirmed success, heals the
subscription back to active with the invoice paid.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from somba.db.models import (
    ChargeAttempt,
    ChargeAttemptStatus,
    Invoice,
    InvoiceStatus,
    LedgerIntent,
    LedgerIntentStatus,
    SubscriptionStatus,
)
from somba.nomba.client import NombaChargeResult, NombaChargeStatus
from somba.workers.charge import worker as charge_worker
from somba.workers.reconcile import verify_pass

UTC = timezone.utc
NOW = datetime(2026, 6, 29, 9, 0, 0, tzinfo=UTC)
PAST = NOW - timedelta(hours=1)


def _mock_debit_uncertain(**kwargs) -> NombaChargeResult:
    return NombaChargeResult(
        status=NombaChargeStatus.uncertain,
        transaction_id=None,
        failure_reason="network_error: timeout",
        response_code=None,
        raw={},
    )


def _mock_verify_succeeded(**kwargs) -> NombaChargeResult:
    return NombaChargeResult(
        status=NombaChargeStatus.succeeded,
        transaction_id="txn-verify-001",
        failure_reason=None,
        response_code="00",
        raw={},
    )


def test_payment_uncertain_resolved_active_by_verify_pass(
    db, merchant_and_token, make_plan, make_customer, make_subscription, monkeypatch
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant, amount=12_000)
    customer = make_customer(merchant)
    customer.mandate_id = "mandate_uncertain_test"
    db.commit()
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=PAST,
        current_period_start=PAST - timedelta(days=30),
        current_period_end=PAST,
    )

    # 1. Bill: Nomba can't confirm the debit -> uncertain.
    monkeypatch.setattr(charge_worker.nomba_client, "debit_mandate", _mock_debit_uncertain)
    written = charge_worker.run(db, cutoff=NOW)
    assert written == 1
    processed = charge_worker.execute_pending(db, now=NOW)
    assert processed == 1

    db.refresh(sub)
    assert sub.status == SubscriptionStatus.payment_uncertain

    attempt = db.scalar(select(ChargeAttempt).where(ChargeAttempt.subscription_id == sub.id))
    assert attempt.status == ChargeAttemptStatus.uncertain

    intent = db.scalar(select(LedgerIntent).where(LedgerIntent.subscription_id == sub.id))
    assert intent.status == LedgerIntentStatus.pending  # left pending for the verify pass

    invoice = db.get(Invoice, intent.invoice_id)
    assert invoice.status == InvoiceStatus.open

    # 2. Verify pass: Nomba now confirms the debit actually succeeded.
    monkeypatch.setattr(verify_pass.nomba_client, "verify_transaction", _mock_verify_succeeded)
    resolved = verify_pass.run(db, now=NOW + timedelta(minutes=20))
    assert resolved == 1

    # 3. Subscription healed back to active, invoice paid, attempt succeeded.
    db.refresh(sub)
    assert sub.status == SubscriptionStatus.active

    db.refresh(attempt)
    assert attempt.status == ChargeAttemptStatus.succeeded

    db.refresh(invoice)
    assert invoice.status == InvoiceStatus.paid


def test_payment_uncertain_confirmed_failed_by_verify_pass_reverts_to_past_due(
    db, merchant_and_token, make_plan, make_customer, make_subscription, monkeypatch
):
    """The mirror case: Nomba confirms the charge actually failed -> past_due, not stuck."""
    merchant, _ = merchant_and_token
    plan = make_plan(merchant, amount=9_000)
    customer = make_customer(merchant)
    customer.mandate_id = "mandate_uncertain_test_2"
    db.commit()
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=PAST,
        current_period_start=PAST - timedelta(days=30),
        current_period_end=PAST,
    )

    monkeypatch.setattr(charge_worker.nomba_client, "debit_mandate", _mock_debit_uncertain)
    charge_worker.run(db, cutoff=NOW)
    charge_worker.execute_pending(db, now=NOW)

    db.refresh(sub)
    assert sub.status == SubscriptionStatus.payment_uncertain

    def _mock_verify_failed(**kwargs) -> NombaChargeResult:
        return NombaChargeResult(
            status=NombaChargeStatus.failed,
            transaction_id=None,
            failure_reason="insufficient_funds",
            response_code="51",
            raw={},
        )

    monkeypatch.setattr(verify_pass.nomba_client, "verify_transaction", _mock_verify_failed)
    resolved = verify_pass.run(db, now=NOW + timedelta(minutes=20))
    assert resolved == 1

    db.refresh(sub)
    assert sub.status == SubscriptionStatus.past_due  # not stuck in payment_uncertain

    intent = db.scalar(select(LedgerIntent).where(LedgerIntent.subscription_id == sub.id))
    assert intent.status == LedgerIntentStatus.unmatched
