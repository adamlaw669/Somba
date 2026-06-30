"""Integration tests for PATCH /v1/subscriptions/:id — plan change with proration."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from somba.db.models import (
    Customer,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    InvoiceType,
    LedgerIntent,
    OutboxEvent,
    SubscriptionStatus,
)

UTC = timezone.utc


def _idem() -> str:
    return uuid.uuid4().hex


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": _idem()}


def _create_sub(api_client, token, plan_id, customer_id):
    resp = api_client.post(
        "/v1/subscriptions",
        json={"plan_id": plan_id, "customer_id": customer_id},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    return resp.json()["subscription"]


# ---------------------------------------------------------------------------
# Upgrade (net positive) — proration invoice + intent created
# ---------------------------------------------------------------------------


def test_upgrade_creates_proration_invoice(
    api_client, merchant_and_token, make_plan, make_customer, db
):
    merchant, token = merchant_and_token
    small_plan = make_plan(merchant, amount=10_000)
    large_plan = make_plan(merchant, amount=30_000)
    customer = make_customer(merchant)

    sub = _create_sub(api_client, token, small_plan.id, customer.id)
    sub_id = sub["id"]

    # Backdate the period so there are real remaining days
    from somba.db.models import Subscription
    s = db.get(Subscription, sub_id)
    now = datetime.now(UTC)
    s.current_period_start = now - timedelta(days=5)
    s.current_period_end = now + timedelta(days=25)
    db.commit()

    resp = api_client.patch(
        f"/v1/subscriptions/{sub_id}",
        json={"plan_id": large_plan.id},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["proration"]["action"] == "charge"
    assert body["proration"]["net_kobo"] > 0
    assert body["subscription"]["plan_id"] == large_plan.id

    # Proration invoice created
    invoices = list(db.scalars(
        select(Invoice).where(
            Invoice.subscription_id == sub_id,
            Invoice.type == InvoiceType.proration,
        )
    ))
    assert len(invoices) == 1
    assert invoices[0].status == InvoiceStatus.open

    # LedgerIntent written for the upgrade charge
    intents = list(db.scalars(
        select(LedgerIntent).where(LedgerIntent.subscription_id == sub_id)
    ))
    assert len(intents) >= 1


def test_upgrade_line_items_written(
    api_client, merchant_and_token, make_plan, make_customer, db
):
    merchant, token = merchant_and_token
    small_plan = make_plan(merchant, amount=10_000)
    large_plan = make_plan(merchant, amount=30_000)
    customer = make_customer(merchant)

    sub = _create_sub(api_client, token, small_plan.id, customer.id)
    sub_id = sub["id"]

    from somba.db.models import Subscription
    s = db.get(Subscription, sub_id)
    now = datetime.now(UTC)
    s.current_period_start = now - timedelta(days=5)
    s.current_period_end = now + timedelta(days=25)
    db.commit()

    api_client.patch(
        f"/v1/subscriptions/{sub_id}",
        json={"plan_id": large_plan.id},
        headers=_auth(token),
    )

    line_items = list(db.scalars(
        select(InvoiceLineItem).join(Invoice).where(Invoice.subscription_id == sub_id)
    ))
    assert len(line_items) == 2
    types = {li.type for li in line_items}
    from somba.db.models import InvoiceLineItemType
    assert InvoiceLineItemType.proration_credit in types
    assert InvoiceLineItemType.proration_charge in types


# ---------------------------------------------------------------------------
# Downgrade (net negative) — credit stored, no immediate charge
# ---------------------------------------------------------------------------


def test_downgrade_stores_credit_balance(
    api_client, merchant_and_token, make_plan, make_customer, db
):
    merchant, token = merchant_and_token
    large_plan = make_plan(merchant, amount=30_000)
    small_plan = make_plan(merchant, amount=10_000)
    customer = make_customer(merchant)

    sub = _create_sub(api_client, token, large_plan.id, customer.id)
    sub_id = sub["id"]

    from somba.db.models import Subscription
    s = db.get(Subscription, sub_id)
    now = datetime.now(UTC)
    s.current_period_start = now - timedelta(days=5)
    s.current_period_end = now + timedelta(days=25)
    db.commit()

    resp = api_client.patch(
        f"/v1/subscriptions/{sub_id}",
        json={"plan_id": small_plan.id},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["proration"]["action"] == "credit"
    assert body["proration"]["net_kobo"] < 0

    db.refresh(customer)
    assert customer.credit_balance > 0


def test_downgrade_publishes_outbox_event(
    api_client, merchant_and_token, make_plan, make_customer, db
):
    merchant, token = merchant_and_token
    large_plan = make_plan(merchant, amount=30_000)
    small_plan = make_plan(merchant, amount=10_000)
    customer = make_customer(merchant)

    sub = _create_sub(api_client, token, large_plan.id, customer.id)
    sub_id = sub["id"]

    from somba.db.models import Subscription
    s = db.get(Subscription, sub_id)
    now = datetime.now(UTC)
    s.current_period_start = now - timedelta(days=5)
    s.current_period_end = now + timedelta(days=25)
    db.commit()

    api_client.patch(
        f"/v1/subscriptions/{sub_id}",
        json={"plan_id": small_plan.id},
        headers=_auth(token),
    )

    events = list(db.scalars(
        select(OutboxEvent).where(OutboxEvent.event_type == "subscription.plan_changed")
    ))
    assert len(events) == 1


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_patch_non_existent_sub_returns_404(api_client, merchant_and_token, make_plan):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)

    resp = api_client.patch(
        "/v1/subscriptions/99999",
        json={"plan_id": plan.id},
        headers=_auth(token),
    )
    assert resp.status_code == 404


def test_patch_same_plan_returns_400(
    api_client, merchant_and_token, make_plan, make_customer
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)

    sub = _create_sub(api_client, token, plan.id, customer.id)

    resp = api_client.patch(
        f"/v1/subscriptions/{sub['id']}",
        json={"plan_id": plan.id},
        headers=_auth(token),
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "no_change"


def test_patch_cross_merchant_plan_returns_404(
    api_client, merchant_and_token, other_merchant_and_token, make_plan, make_customer
):
    merchant, token = merchant_and_token
    other_merchant, _ = other_merchant_and_token

    plan = make_plan(merchant)
    other_plan = make_plan(other_merchant)
    customer = make_customer(merchant)

    sub = _create_sub(api_client, token, plan.id, customer.id)

    resp = api_client.patch(
        f"/v1/subscriptions/{sub['id']}",
        json={"plan_id": other_plan.id},
        headers=_auth(token),
    )
    assert resp.status_code == 404


def test_patch_unauthenticated_returns_401(
    api_client, merchant_and_token, make_plan, make_customer
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    plan2 = make_plan(merchant, name="Plan 2", amount=20_000)
    customer = make_customer(merchant)

    sub = _create_sub(api_client, token, plan.id, customer.id)

    resp = api_client.patch(
        f"/v1/subscriptions/{sub['id']}",
        json={"plan_id": plan2.id},
        headers={"Idempotency-Key": _idem()},
    )
    assert resp.status_code == 401
