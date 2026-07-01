"""ChargeAttempt.order_reference is unique per row, but every attempt on the
same LedgerIntent used to reuse the intent's own order_reference verbatim --
so a second attempt (a retry, or reprocessing after "uncertain") crashed with
a UniqueViolation, silently aborting the whole execute_pending() batch. Found
live: a leftover "uncertain" intent from an earlier run got reprocessed and
crashed exactly this way.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from somba.db.models import ChargeAttempt, LedgerIntent, SubscriptionStatus
from somba.nomba.client import NombaChargeResult, NombaChargeStatus
from somba.workers.charge import worker as charge_worker
from somba.workers.charge.worker import execute_pending
from somba.workers.charge.worker import run as billing_run

UTC = timezone.utc
NOW = datetime(2026, 6, 28, 12, 0, 0, tzinfo=UTC)
PAST = NOW - timedelta(hours=1)


def test_second_attempt_on_same_intent_does_not_collide_on_order_reference(
    db, merchant_and_token, make_plan, make_customer, make_subscription, monkeypatch
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant, amount=5000)
    customer = make_customer(merchant)
    customer.mandate_id = "mandate-retry-test"
    db.commit()
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=PAST,
        current_period_start=PAST - timedelta(days=30),
        current_period_end=PAST,
    )

    billing_run(db, cutoff=NOW)
    intent = db.scalar(select(LedgerIntent).where(LedgerIntent.subscription_id == sub.id))

    # Attempt 1: uncertain -- intent stays pending so it gets reprocessed.
    def fake_uncertain(**kwargs):
        return NombaChargeResult(
            status=NombaChargeStatus.uncertain, transaction_id=None,
            failure_reason="network_error: timeout", response_code=None,
        )

    monkeypatch.setattr(charge_worker.nomba_client, "debit_mandate", fake_uncertain)
    execute_pending(db, now=NOW)

    db.refresh(intent)
    assert intent.status.value == "pending"

    # Attempt 2: this must not crash with a UniqueViolation on order_reference.
    def fake_success(**kwargs):
        return NombaChargeResult(
            status=NombaChargeStatus.succeeded, transaction_id="txn-retry-2",
            failure_reason=None, response_code="00",
        )

    monkeypatch.setattr(charge_worker.nomba_client, "debit_mandate", fake_success)
    execute_pending(db, now=NOW + timedelta(minutes=5))

    attempts = list(
        db.scalars(select(ChargeAttempt).where(ChargeAttempt.subscription_id == sub.id).order_by(ChargeAttempt.attempt_number))
    )
    assert len(attempts) == 2
    assert attempts[0].order_reference != attempts[1].order_reference
    assert attempts[1].status.value == "succeeded"

    db.refresh(intent)
    assert intent.status.value == "matched"
