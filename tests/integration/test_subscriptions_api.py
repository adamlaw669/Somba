"""Integration tests for POST /v1/subscriptions and GET /v1/subscriptions."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from somba.db.models import (
    OutboxEvent,
    PlanStatus,
    Subscription,
    SubscriptionEvent,
    SubscriptionStatus,
)

UTC = timezone.utc


def _idem() -> str:
    return uuid.uuid4().hex


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": _idem()}


# ---------------------------------------------------------------------------
# POST /v1/subscriptions — happy path
# ---------------------------------------------------------------------------


def test_create_subscription_active_no_trial(api_client, merchant_and_token, make_plan, make_customer, db):
    merchant, token = merchant_and_token
    plan = make_plan(merchant, amount=5_000)
    customer = make_customer(merchant)

    resp = api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan.id, "customer_id": customer.id},
        headers=_auth(token),
    )

    assert resp.status_code == 201
    body = resp.json()["subscription"]
    assert body["status"] == "active"
    assert body["plan_id"] == plan.id
    assert body["customer_id"] == customer.id
    assert body["next_bill_date"] is not None


def test_create_subscription_trialing_when_plan_has_trial_days(
    api_client, merchant_and_token, make_customer, db
):
    from somba.db.models import Plan

    merchant, token = merchant_and_token
    plan = Plan(
        merchant_id=merchant.id,
        name="Trial Plan",
        amount=10_000,
        currency="NGN",
        interval="month",
        interval_count=1,
        trial_days=7,
        status=PlanStatus.active,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    customer = make_customer(merchant)

    resp = api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan.id, "customer_id": customer.id},
        headers=_auth(token),
    )

    assert resp.status_code == 201
    body = resp.json()["subscription"]
    assert body["status"] == "trialing"
    assert body["trial_end"] is not None


def test_create_subscription_with_explicit_trial_end(
    api_client, merchant_and_token, make_plan, make_customer
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    trial_end = (datetime.now(UTC) + timedelta(days=14)).isoformat()

    resp = api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan.id, "customer_id": customer.id, "trial_end": trial_end},
        headers=_auth(token),
    )

    assert resp.status_code == 201
    body = resp.json()["subscription"]
    assert body["status"] == "trialing"


def test_create_subscription_writes_subscription_event(
    api_client, merchant_and_token, make_plan, make_customer, db
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan.id, "customer_id": customer.id},
        headers=_auth(token),
    )

    events = list(db.scalars(select(SubscriptionEvent)))
    assert len(events) == 1
    assert events[0].to_status == "active"
    assert events[0].trigger.value == "api"


def test_create_subscription_publishes_outbox_event(
    api_client, merchant_and_token, make_plan, make_customer, db
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan.id, "customer_id": customer.id},
        headers=_auth(token),
    )

    events = list(db.scalars(select(OutboxEvent).where(OutboxEvent.event_type == "subscription.created")))
    assert len(events) == 1


# ---------------------------------------------------------------------------
# POST /v1/subscriptions — error cases
# ---------------------------------------------------------------------------


def test_create_subscription_wrong_plan_returns_404(
    api_client, merchant_and_token, make_customer
):
    merchant, token = merchant_and_token
    customer = make_customer(merchant)

    resp = api_client.post(
        "/v1/subscriptions",
        json={"plan_id": 99999, "customer_id": customer.id},
        headers=_auth(token),
    )
    assert resp.status_code == 404


def test_create_subscription_wrong_customer_returns_404(
    api_client, merchant_and_token, make_plan
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)

    resp = api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan.id, "customer_id": 99999},
        headers=_auth(token),
    )
    assert resp.status_code == 404


def test_create_subscription_archived_plan_returns_400(
    api_client, merchant_and_token, make_plan, make_customer
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant, status=PlanStatus.archived)
    customer = make_customer(merchant)

    resp = api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan.id, "customer_id": customer.id},
        headers=_auth(token),
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "plan_archived"


def test_create_subscription_unauthenticated_returns_401(api_client, make_plan, make_customer, merchant_and_token):
    merchant, _ = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    resp = api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan.id, "customer_id": customer.id},
        headers={"Idempotency-Key": _idem()},
    )
    assert resp.status_code == 401


def test_create_subscription_missing_idempotency_key_returns_400(
    api_client, merchant_and_token, make_plan, make_customer
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    resp = api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan.id, "customer_id": customer.id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "missing_idempotency_key"


# ---------------------------------------------------------------------------
# Merchant isolation: cannot use another merchant's plan or customer
# ---------------------------------------------------------------------------


def test_create_subscription_cross_merchant_plan_returns_404(
    api_client, merchant_and_token, other_merchant_and_token, make_plan, make_customer
):
    merchant, token = merchant_and_token
    other_merchant, _ = other_merchant_and_token

    other_plan = make_plan(other_merchant)
    customer = make_customer(merchant)

    resp = api_client.post(
        "/v1/subscriptions",
        json={"plan_id": other_plan.id, "customer_id": customer.id},
        headers=_auth(token),
    )
    assert resp.status_code == 404


def test_create_subscription_cross_merchant_customer_returns_404(
    api_client, merchant_and_token, other_merchant_and_token, make_plan, make_customer
):
    merchant, token = merchant_and_token
    other_merchant, _ = other_merchant_and_token

    plan = make_plan(merchant)
    other_customer = make_customer(other_merchant)

    resp = api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan.id, "customer_id": other_customer.id},
        headers=_auth(token),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /v1/subscriptions
# ---------------------------------------------------------------------------


def test_list_subscriptions_returns_merchant_subscriptions(
    api_client, merchant_and_token, make_plan, make_customer
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    for _ in range(2):
        api_client.post(
            "/v1/subscriptions",
            json={"plan_id": plan.id, "customer_id": customer.id},
            headers=_auth(token),
        )

    resp = api_client.get("/v1/subscriptions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()["subscriptions"]) == 2


def test_list_subscriptions_excludes_other_merchant(
    api_client, merchant_and_token, other_merchant_and_token, make_plan, make_customer
):
    merchant, token = merchant_and_token
    other_merchant, other_token = other_merchant_and_token

    plan = make_plan(merchant)
    other_plan = make_plan(other_merchant)
    customer = make_customer(merchant)
    other_customer = make_customer(other_merchant)

    api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan.id, "customer_id": customer.id},
        headers=_auth(token),
    )
    api_client.post(
        "/v1/subscriptions",
        json={"plan_id": other_plan.id, "customer_id": other_customer.id},
        headers=_auth(other_token),
    )

    resp = api_client.get("/v1/subscriptions", headers={"Authorization": f"Bearer {token}"})
    subs = resp.json()["subscriptions"]
    assert len(subs) == 1
    assert subs[0]["merchant_id"] == merchant.id


def test_get_subscription_by_id(api_client, merchant_and_token, make_plan, make_customer):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    create_resp = api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan.id, "customer_id": customer.id},
        headers=_auth(token),
    )
    sub_id = create_resp.json()["subscription"]["id"]

    resp = api_client.get(f"/v1/subscriptions/{sub_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["subscription"]["id"] == sub_id


def test_get_subscription_wrong_merchant_returns_404(
    api_client, merchant_and_token, other_merchant_and_token, make_plan, make_customer
):
    merchant, token = merchant_and_token
    other_merchant, other_token = other_merchant_and_token

    plan = make_plan(merchant)
    customer = make_customer(merchant)

    create_resp = api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan.id, "customer_id": customer.id},
        headers=_auth(token),
    )
    sub_id = create_resp.json()["subscription"]["id"]

    resp = api_client.get(f"/v1/subscriptions/{sub_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert resp.status_code == 404
