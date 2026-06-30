"""Correctness tests: double-charge impossibility and intent-before-Nomba (crash sim).

Guards the PRD's hardest invariants:
  - Zero double charges (billing lock + intent status + charge-attempt key).
  - RPO=0 on the charge path: the ledger intent is durably written BEFORE the
    Nomba call, so a crash mid-charge loses nothing and stays recoverable.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from somba.db.models import (
    ChargeAttempt,
    LedgerIntent,
    LedgerIntentStatus,
    SubscriptionStatus,
)
from somba.nomba.client import NombaChargeResult, NombaChargeStatus
from somba.workers.charge import worker as charge_worker
from somba.workers.charge.worker import execute_pending, run

UTC = timezone.utc
NOW = datetime(2026, 6, 28, 12, 0, 0, tzinfo=UTC)
PAST = NOW - timedelta(hours=1)


def _due_sub_with_mandate(db, make_plan, make_customer, make_subscription, merchant):
    plan = make_plan(merchant, amount=10_000)
    customer = make_customer(merchant)
    customer.mandate_id = "mandate_test"  # Phase 2 needs a mandate to charge
    db.commit()
    return make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=PAST,
        current_period_start=PAST - timedelta(days=30),
        current_period_end=PAST,
    )


def _count(db, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def test_double_charge_impossible_on_repeated_full_run(
    db, merchant_and_token, make_plan, make_customer, make_subscription, monkeypatch
):
    """Running sweep + execute TWICE charges exactly once."""
    merchant, _ = merchant_and_token
    _due_sub_with_mandate(db, make_plan, make_customer, make_subscription, merchant)

    calls = {"n": 0}

    def fake_debit(*, mandate_id, amount_kobo, base_url=None):
        calls["n"] += 1
        return NombaChargeResult(
            status=NombaChargeStatus.succeeded,
            transaction_id="txn_1",
            failure_reason=None,
            response_code=None,
        )

    monkeypatch.setattr(charge_worker.nomba_client, "debit_mandate", fake_debit)

    # Fire the entire billing flow twice (scheduler + worker both running twice).
    for _ in range(2):
        run(db, cutoff=NOW)
        execute_pending(db, now=NOW)

    assert calls["n"] == 1, f"Nomba was debited {calls['n']}x — double charge!"
    assert _count(db, LedgerIntent) == 1     # billing lock -> one intent per period
    assert _count(db, ChargeAttempt) == 1    # intent went terminal -> not re-charged


def test_intent_written_before_nomba_call_survives_crash(
    db, merchant_and_token, make_plan, make_customer, make_subscription, monkeypatch
):
    """A crash AT the Nomba call leaves the intent durably pending (RPO=0)."""
    merchant, _ = merchant_and_token
    sub = _due_sub_with_mandate(db, make_plan, make_customer, make_subscription, merchant)

    # Phase 1 writes + commits the intent BEFORE any Nomba call happens.
    run(db, cutoff=NOW)
    intent = db.scalar(select(LedgerIntent).where(LedgerIntent.subscription_id == sub.id))
    assert intent is not None
    assert intent.status == LedgerIntentStatus.pending

    # Crash exactly at the Nomba call.
    called = {"n": 0}

    def boom(*, mandate_id, amount_kobo, base_url=None):
        called["n"] += 1
        raise RuntimeError("simulated crash during Nomba call")

    monkeypatch.setattr(charge_worker.nomba_client, "debit_mandate", boom)

    with pytest.raises(RuntimeError):
        execute_pending(db, now=NOW)

    # We reached the Nomba seam — proving the intent was written before the call.
    assert called["n"] == 1

    # The intent survived the crash, still pending -> recoverable on restart.
    db.expire_all()
    survivor = db.scalar(select(LedgerIntent).where(LedgerIntent.subscription_id == sub.id))
    assert survivor is not None
    assert survivor.status == LedgerIntentStatus.pending

    # No charge attempt recorded — the crash happened before _handle_success/_failure.
    assert _count(db, ChargeAttempt) == 0
