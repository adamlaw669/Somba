"""Integration tests for billing sweep query and billing lock.

Tests verify which subscriptions are selected for billing and that the
billing lock behaves correctly under concurrent-style duplicate inserts.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from somba.db.models import BillingLock, BillingLockStatus, SubscriptionStatus
from somba.scheduler.billing_sweep import acquire_billing_lock, fetch_due_subscriptions

UTC = timezone.utc
NOW = datetime(2026, 6, 28, 12, 0, 0, tzinfo=UTC)
PAST = NOW - timedelta(hours=1)
FUTURE = NOW + timedelta(hours=1)


# ---------------------------------------------------------------------------
# fetch_due_subscriptions
# ---------------------------------------------------------------------------


def test_active_subscription_past_due_is_returned(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=PAST,
    )

    results = fetch_due_subscriptions(db, cutoff=NOW)

    assert len(results) == 1
    assert results[0].id == sub.id


def test_trialing_subscription_past_due_is_returned(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.trialing,
        next_bill_date=PAST,
    )

    results = fetch_due_subscriptions(db, cutoff=NOW)
    assert any(r.id == sub.id for r in results)


def test_active_subscription_due_exactly_at_cutoff_is_returned(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=NOW,
    )

    results = fetch_due_subscriptions(db, cutoff=NOW)
    assert len(results) == 1


def test_active_subscription_with_future_date_is_not_returned(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=FUTURE,
    )

    results = fetch_due_subscriptions(db, cutoff=NOW)
    assert results == []


@pytest.mark.parametrize("excluded_status", [
    SubscriptionStatus.past_due,
    SubscriptionStatus.payment_uncertain,
    SubscriptionStatus.paused,
    SubscriptionStatus.cancelled,
    SubscriptionStatus.expired,
])
def test_non_billable_statuses_are_excluded(
    excluded_status, db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    make_subscription(
        merchant, customer, plan,
        status=excluded_status,
        next_bill_date=PAST,
    )

    results = fetch_due_subscriptions(db, cutoff=NOW)
    assert results == [], f"Expected {excluded_status.value} to be excluded but got results"


def test_results_ordered_by_next_bill_date_ascending(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    dates = [
        NOW - timedelta(hours=3),
        NOW - timedelta(hours=1),
        NOW - timedelta(hours=2),
    ]
    for d in dates:
        make_subscription(
            merchant, customer, plan,
            status=SubscriptionStatus.active,
            next_bill_date=d,
        )

    results = fetch_due_subscriptions(db, cutoff=NOW)
    assert len(results) == 3
    for i in range(len(results) - 1):
        assert results[i].next_bill_date <= results[i + 1].next_bill_date


def test_limit_caps_returned_rows(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    for _ in range(5):
        make_subscription(
            merchant, customer, plan,
            status=SubscriptionStatus.active,
            next_bill_date=PAST,
        )

    results = fetch_due_subscriptions(db, cutoff=NOW, limit=3)
    assert len(results) == 3


def test_subscription_without_next_bill_date_is_excluded(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    make_subscription(
        merchant, customer, plan,
        status=SubscriptionStatus.active,
        next_bill_date=None,
    )

    results = fetch_due_subscriptions(db, cutoff=NOW)
    assert results == []


# ---------------------------------------------------------------------------
# acquire_billing_lock
# ---------------------------------------------------------------------------


def test_acquire_billing_lock_returns_true_on_first_call(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)

    acquired = acquire_billing_lock(db, sub.id, date(2026, 6, 28))
    assert acquired is True


def test_acquire_billing_lock_persists_lock_row(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)

    acquire_billing_lock(db, sub.id, date(2026, 6, 28))

    lock = db.scalar(
        select(BillingLock).where(
            BillingLock.subscription_id == sub.id,
            BillingLock.billing_period == date(2026, 6, 28),
        )
    )
    assert lock is not None
    assert lock.status == BillingLockStatus.locked


def test_acquire_billing_lock_returns_false_on_second_call(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)

    period = date(2026, 6, 28)
    first = acquire_billing_lock(db, sub.id, period)
    second = acquire_billing_lock(db, sub.id, period)

    assert first is True
    assert second is False


def test_acquire_billing_lock_different_period_is_independent(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)

    june = date(2026, 6, 1)
    july = date(2026, 7, 1)

    assert acquire_billing_lock(db, sub.id, june) is True
    assert acquire_billing_lock(db, sub.id, june) is False
    assert acquire_billing_lock(db, sub.id, july) is True


def test_acquire_billing_lock_different_subscription_is_independent(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    sub_a = make_subscription(merchant, customer, plan)
    sub_b = make_subscription(merchant, customer, plan)

    period = date(2026, 6, 28)
    assert acquire_billing_lock(db, sub_a.id, period) is True
    assert acquire_billing_lock(db, sub_b.id, period) is True


def test_lock_count_after_multiple_attempts_remains_one(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)

    period = date(2026, 6, 28)
    acquire_billing_lock(db, sub.id, period)
    acquire_billing_lock(db, sub.id, period)
    acquire_billing_lock(db, sub.id, period)

    count = db.query(BillingLock).filter(
        BillingLock.subscription_id == sub.id,
        BillingLock.billing_period == period,
    ).count()
    assert count == 1
