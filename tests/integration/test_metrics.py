"""/v1/metrics: recovery_rate — of every time a subscription entered
past_due, what fraction eventually recovered back to active."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from somba.db.models import SubscriptionEventTrigger, SubscriptionStatus
from somba.subscriptions.state_machine import transition

UTC = timezone.utc
NOW = datetime(2026, 6, 30, 12, 0, 0, tzinfo=UTC)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_metrics(api_client, token: str) -> dict:
    resp = api_client.get("/v1/metrics", headers=_auth(token))
    assert resp.status_code == 200
    return resp.json()["metrics"]


def test_recovery_rate_none_with_no_past_due_history(api_client, merchant_and_token):
    _, token = merchant_and_token
    m = _get_metrics(api_client, token)
    assert m["past_due_total"] == 0
    assert m["past_due_healed"] == 0
    assert m["recovery_rate"] is None


def test_recovery_rate_full_after_single_heal(
    api_client, db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan, status=SubscriptionStatus.active)

    transition(sub, SubscriptionStatus.past_due, SubscriptionEventTrigger.scheduler, db)
    db.commit()
    transition(sub, SubscriptionStatus.active, SubscriptionEventTrigger.reconciliation, db)
    db.commit()

    m = _get_metrics(api_client, token)
    assert m["past_due_total"] == 1
    assert m["past_due_healed"] == 1
    assert m["recovery_rate"] == 1.0


def test_recovery_rate_half_when_one_of_two_heals(
    api_client, db, merchant_and_token, make_plan, make_customer, make_subscription
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    healed_sub = make_subscription(merchant, customer, plan, status=SubscriptionStatus.active)
    transition(healed_sub, SubscriptionStatus.past_due, SubscriptionEventTrigger.scheduler, db)
    db.commit()
    transition(healed_sub, SubscriptionStatus.active, SubscriptionEventTrigger.reconciliation, db)
    db.commit()

    stuck_sub = make_subscription(merchant, customer, plan, status=SubscriptionStatus.active)
    transition(stuck_sub, SubscriptionStatus.past_due, SubscriptionEventTrigger.scheduler, db)
    db.commit()

    m = _get_metrics(api_client, token)
    assert m["past_due_total"] == 2
    assert m["past_due_healed"] == 1
    assert m["recovery_rate"] == 0.5


def test_recovery_rate_isolated_per_merchant(
    api_client, db, merchant_and_token, other_merchant_and_token,
    make_plan, make_customer, make_subscription,
):
    merchant, token = merchant_and_token
    other_merchant, _ = other_merchant_and_token

    # Other merchant has past_due history that must not leak into this one's rate.
    other_plan = make_plan(other_merchant)
    other_customer = make_customer(other_merchant, email="theirs@gym.com")
    other_sub = make_subscription(other_merchant, other_customer, other_plan, status=SubscriptionStatus.active)
    transition(other_sub, SubscriptionStatus.past_due, SubscriptionEventTrigger.scheduler, db)
    db.commit()

    m = _get_metrics(api_client, token)
    assert m["past_due_total"] == 0
    assert m["past_due_healed"] == 0
    assert m["recovery_rate"] is None
