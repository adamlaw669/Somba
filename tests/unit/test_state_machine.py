"""Unit tests for the subscription state machine.

Each test verifies observable outcomes: status changes on the subscription
row, SubscriptionEvent rows written to the DB, and IllegalTransitionError
raised with no side-effects on invalid moves.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from somba.db.models import SubscriptionEvent, SubscriptionEventTrigger, SubscriptionStatus
from somba.subscriptions.state_machine import (
    VALID_TRANSITIONS,
    IllegalTransitionError,
    transition,
)

S = SubscriptionStatus
T = SubscriptionEventTrigger

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count_events(db, subscription_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(SubscriptionEvent).where(
            SubscriptionEvent.subscription_id == subscription_id
        )
    ) or 0


def _last_event(db, subscription_id: int) -> SubscriptionEvent | None:
    return db.scalar(
        select(SubscriptionEvent)
        .where(SubscriptionEvent.subscription_id == subscription_id)
        .order_by(SubscriptionEvent.id.desc())
    )


# ---------------------------------------------------------------------------
# Table completeness
# ---------------------------------------------------------------------------


def test_transition_table_covers_all_seven_states():
    assert set(VALID_TRANSITIONS.keys()) == set(S)


def test_terminal_states_have_empty_allowed_set():
    assert VALID_TRANSITIONS[S.cancelled] == frozenset()
    assert VALID_TRANSITIONS[S.expired] == frozenset()


# ---------------------------------------------------------------------------
# Valid transitions — parametrized exhaustively from VALID_TRANSITIONS
# ---------------------------------------------------------------------------

_ALL_VALID = [
    (from_s, to_s)
    for from_s, targets in VALID_TRANSITIONS.items()
    for to_s in targets
]


@pytest.mark.parametrize("from_status,to_status", _ALL_VALID, ids=lambda s: s.value)
def test_valid_transition_updates_subscription_status(
    from_status, to_status, db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan, status=from_status)

    transition(sub, to_status, T.api, db)
    db.commit()
    db.refresh(sub)

    assert sub.status == to_status


@pytest.mark.parametrize("from_status,to_status", _ALL_VALID, ids=lambda s: s.value)
def test_valid_transition_writes_subscription_event(
    from_status, to_status, db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan, status=from_status)

    transition(sub, to_status, T.scheduler, db)
    db.commit()

    event = _last_event(db, sub.id)
    assert event is not None
    assert event.from_status == from_status.value
    assert event.to_status == to_status.value
    assert event.trigger == T.scheduler
    assert event.merchant_id == merchant.id
    assert event.subscription_id == sub.id


def test_transition_stores_metadata_in_event(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan, status=S.active)

    meta = {"invoice_id": 42, "reason": "dunning"}
    transition(sub, S.past_due, T.scheduler, db, metadata=meta)
    db.commit()

    event = _last_event(db, sub.id)
    assert event.metadata_ == meta


def test_transition_stores_empty_metadata_when_none_given(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan, status=S.active)

    transition(sub, S.past_due, T.api, db, metadata=None)
    db.commit()

    event = _last_event(db, sub.id)
    assert event.metadata_ == {}


# ---------------------------------------------------------------------------
# Illegal transitions
# ---------------------------------------------------------------------------

_ILLEGAL = [
    (S.cancelled, S.active),
    (S.cancelled, S.trialing),
    (S.cancelled, S.past_due),
    (S.cancelled, S.paused),
    (S.expired, S.active),
    (S.expired, S.trialing),
    (S.expired, S.past_due),
    (S.active, S.trialing),          # no going backwards
    (S.trialing, S.payment_uncertain),  # must go through active/past_due first
    (S.trialing, S.paused),
    (S.paused, S.past_due),
    (S.paused, S.payment_uncertain),
    (S.payment_uncertain, S.paused),
    (S.payment_uncertain, S.expired),
]


@pytest.mark.parametrize("from_status,to_status", _ILLEGAL, ids=lambda s: s.value)
def test_illegal_transition_raises(
    from_status, to_status, db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan, status=from_status)

    with pytest.raises(IllegalTransitionError):
        transition(sub, to_status, T.api, db)


@pytest.mark.parametrize("from_status,to_status", _ILLEGAL, ids=lambda s: s.value)
def test_illegal_transition_does_not_write_event(
    from_status, to_status, db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan, status=from_status)

    try:
        transition(sub, to_status, T.api, db)
    except IllegalTransitionError:
        pass

    db.commit()
    assert _count_events(db, sub.id) == 0


@pytest.mark.parametrize("from_status,to_status", _ILLEGAL, ids=lambda s: s.value)
def test_illegal_transition_does_not_change_status(
    from_status, to_status, db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan, status=from_status)

    try:
        transition(sub, to_status, T.api, db)
    except IllegalTransitionError:
        pass

    db.refresh(sub)
    assert sub.status == from_status


# ---------------------------------------------------------------------------
# Multiple sequential transitions
# ---------------------------------------------------------------------------


def test_multiple_transitions_each_write_an_event(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan, status=S.trialing)

    transition(sub, S.active, T.scheduler, db)
    transition(sub, S.past_due, T.scheduler, db)
    transition(sub, S.active, T.reconciliation, db)
    db.commit()

    assert _count_events(db, sub.id) == 3
    assert sub.status == S.active


def test_each_trigger_type_is_stored_correctly(
    db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    for trigger in T:
        sub = make_subscription(merchant, customer, plan, status=S.active)
        transition(sub, S.past_due, trigger, db)
        db.commit()
        event = _last_event(db, sub.id)
        assert event.trigger == trigger
        # reset for next iteration
        sub.status = S.active
        db.commit()

