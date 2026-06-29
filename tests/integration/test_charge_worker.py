"""Integration tests for the charge worker.

Tests verify that run() creates LedgerIntent rows, acquires billing locks,
is idempotent on repeated calls, and correctly skips ineligible subscriptions.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from somba.db.models import BillingLock, Invoice, LedgerIntent, LedgerIntentStatus, SubscriptionStatus
from somba.workers.charge.worker import run

UTC = timezone.utc
NOW = datetime(2026, 6, 28, 12, 0, 0, tzinfo=UTC)
PAST = NOW - timedelta(hours=1)
FUTURE = NOW + timedelta(days=30)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _intents_for(db, subscription_id: int) -> list[LedgerIntent]:
    return list(
        db.scalars(
            select(LedgerIntent).where(LedgerIntent.subscription_id == subscription_id)
        )
    )


def _invoices_for(db, subscription_id: int) -> list[Invoice]:
    return list(
        db.scalars(
            select(Invoice).where(Invoice.subscription_id == subscription_id)
        )
    )


def _locks_for(db, subscription_id: int) -> list[BillingLock]:
    return list(
        db.scalars(
            select(BillingLock).where(BillingLock.subscription_id == subscription_id)
        )
    )


# ---------------------------------------------------------------------------
# Basic intent creation
# ---------------------------------------------------------------------------


def test_run_writes_ledger_intent_for_due_subscription(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant, amount=10_000)
    customer = make_customer(merchant)
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=PAST,
        current_period_start=PAST - timedelta(days=30),
        current_period_end=PAST,
    )

    written = run(db, cutoff=NOW)

    assert written == 1
    intents = _intents_for(db, sub.id)
    assert len(intents) == 1
    intent = intents[0]
    assert intent.status == LedgerIntentStatus.pending
    assert intent.amount == 10_000
    assert intent.merchant_id == merchant.id
    assert intent.subscription_id == sub.id


def test_run_creates_invoice_for_due_subscription(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant, amount=5_000)
    customer = make_customer(merchant)
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=PAST,
        current_period_start=PAST - timedelta(days=30),
        current_period_end=PAST,
    )

    run(db, cutoff=NOW)

    invoices = _invoices_for(db, sub.id)
    assert len(invoices) == 1
    assert invoices[0].amount == 5_000
    assert invoices[0].customer_id == customer.id
    assert invoices[0].merchant_id == merchant.id


def test_run_acquires_billing_lock_for_processed_subscription(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=PAST,
        current_period_start=PAST - timedelta(days=30),
        current_period_end=PAST,
    )

    run(db, cutoff=NOW)

    locks = _locks_for(db, sub.id)
    assert len(locks) == 1


def test_run_returns_count_of_written_intents(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    for _ in range(3):
        make_subscription(
            merchant, customer, plan,
            status=SubscriptionStatus.active,
            next_bill_date=PAST,
            current_period_start=PAST - timedelta(days=30),
            current_period_end=PAST,
        )

    written = run(db, cutoff=NOW)
    assert written == 3


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_run_is_idempotent_second_call_writes_no_new_intents(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=PAST,
        current_period_start=PAST - timedelta(days=30),
        current_period_end=PAST,
    )

    first = run(db, cutoff=NOW)
    second = run(db, cutoff=NOW)

    assert first == 1
    assert second == 0
    assert len(_intents_for(db, sub.id)) == 1


def test_run_idempotent_intent_idempotency_key_is_unique(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    """Two runs produce exactly one intent with one unique idempotency key."""
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=PAST,
        current_period_start=PAST - timedelta(days=30),
        current_period_end=PAST,
    )

    run(db, cutoff=NOW)
    run(db, cutoff=NOW)

    intents = _intents_for(db, sub.id)
    assert len(intents) == 1
    idem_keys = {i.idempotency_key for i in intents}
    assert len(idem_keys) == 1  # no duplicates


# ---------------------------------------------------------------------------
# Eligibility filtering
# ---------------------------------------------------------------------------


def test_run_skips_future_subscriptions(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=FUTURE,
    )

    written = run(db, cutoff=NOW)
    assert written == 0
    assert _intents_for(db, sub.id) == []


@pytest.mark.parametrize("excluded_status", [
    SubscriptionStatus.past_due,
    SubscriptionStatus.paused,
    SubscriptionStatus.cancelled,
    SubscriptionStatus.expired,
    SubscriptionStatus.payment_uncertain,
])
def test_run_skips_non_billable_status(
    excluded_status, db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(
        merchant, customer, plan,
        status=excluded_status,
        next_bill_date=PAST,
    )

    written = run(db, cutoff=NOW)
    assert written == 0
    assert _intents_for(db, sub.id) == []


def test_run_skips_subscription_where_lock_already_held(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    """Pre-existing billing lock prevents intent from being written."""
    from datetime import date
    from somba.scheduler.billing_sweep import acquire_billing_lock

    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=PAST,
        current_period_start=PAST - timedelta(days=30),
        current_period_end=PAST,
    )

    # Simulate another worker already holding the lock for today
    acquire_billing_lock(db, sub.id, NOW.date())

    written = run(db, cutoff=NOW)
    assert written == 0
    assert _intents_for(db, sub.id) == []


# ---------------------------------------------------------------------------
# Multiple subscriptions — partial eligibility
# ---------------------------------------------------------------------------


def test_run_processes_eligible_and_skips_ineligible_in_same_batch(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    due_sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=PAST,
        current_period_start=PAST - timedelta(days=30),
        current_period_end=PAST,
    )
    _future_sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=FUTURE,
    )
    _cancelled_sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.cancelled,
        next_bill_date=PAST,
    )

    written = run(db, cutoff=NOW)
    assert written == 1
    assert len(_intents_for(db, due_sub.id)) == 1
