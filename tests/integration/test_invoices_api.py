"""Integration tests for GET /v1/invoices and GET /v1/invoices/:id."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from somba.db.models import Invoice, InvoiceLineItem, InvoiceLineItemType, InvoiceStatus, InvoiceType

UTC = timezone.utc


def _idem() -> str:
    return uuid.uuid4().hex


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": _idem()}


def _make_invoice(db, merchant, customer, sub, *, amount=10_000, status=InvoiceStatus.open):
    now = datetime.now(UTC)
    invoice = Invoice(
        merchant_id=merchant.id,
        subscription_id=sub.id,
        customer_id=customer.id,
        amount=amount,
        status=status,
        type=InvoiceType.regular,
        period_start=now - timedelta(days=30),
        period_end=now,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


# ---------------------------------------------------------------------------
# List invoices
# ---------------------------------------------------------------------------


def test_list_invoices_returns_merchant_invoices(
    api_client, merchant_and_token, make_plan, make_customer, make_subscription, db
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)
    inv = _make_invoice(db, merchant, customer, sub)

    resp = api_client.get("/v1/invoices", headers=_auth(token))
    assert resp.status_code == 200
    ids = [i["id"] for i in resp.json()["invoices"]]
    assert inv.id in ids


def test_list_invoices_scoped_to_merchant(
    api_client, merchant_and_token, other_merchant_and_token,
    make_plan, make_customer, make_subscription, db
):
    merchant, token = merchant_and_token
    other_merchant, other_token = other_merchant_and_token

    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)
    inv = _make_invoice(db, merchant, customer, sub)

    resp = api_client.get("/v1/invoices", headers=_auth(other_token))
    ids = [i["id"] for i in resp.json()["invoices"]]
    assert inv.id not in ids


def test_list_invoices_filter_by_subscription(
    api_client, merchant_and_token, make_plan, make_customer, make_subscription, db
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub1 = make_subscription(merchant, customer, plan)
    sub2 = make_subscription(merchant, customer, plan)
    inv1 = _make_invoice(db, merchant, customer, sub1)
    inv2 = _make_invoice(db, merchant, customer, sub2)

    resp = api_client.get(f"/v1/invoices?subscription_id={sub1.id}", headers=_auth(token))
    ids = [i["id"] for i in resp.json()["invoices"]]
    assert inv1.id in ids
    assert inv2.id not in ids


def test_list_invoices_unauthenticated_returns_401(api_client):
    resp = api_client.get("/v1/invoices", headers={"Idempotency-Key": _idem()})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Get invoice by id
# ---------------------------------------------------------------------------


def test_get_invoice_returns_invoice(
    api_client, merchant_and_token, make_plan, make_customer, make_subscription, db
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)
    inv = _make_invoice(db, merchant, customer, sub, amount=15_000)

    resp = api_client.get(f"/v1/invoices/{inv.id}", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()["invoice"]
    assert body["id"] == inv.id
    assert body["amount"] == 15_000
    assert body["status"] == "open"


def test_get_invoice_includes_line_items(
    api_client, merchant_and_token, make_plan, make_customer, make_subscription, db
):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)
    inv = _make_invoice(db, merchant, customer, sub)

    li = InvoiceLineItem(
        invoice_id=inv.id,
        merchant_id=merchant.id,
        type=InvoiceLineItemType.subscription,
        description="Monthly subscription",
        amount=10_000,
    )
    db.add(li)
    db.commit()

    resp = api_client.get(f"/v1/invoices/{inv.id}", headers=_auth(token))
    assert resp.status_code == 200
    line_items = resp.json()["invoice"]["line_items"]
    assert len(line_items) == 1
    assert line_items[0]["type"] == "subscription"


def test_get_invoice_cross_merchant_returns_404(
    api_client, merchant_and_token, other_merchant_and_token,
    make_plan, make_customer, make_subscription, db
):
    merchant, token = merchant_and_token
    other_merchant, other_token = other_merchant_and_token

    plan = make_plan(merchant)
    customer = make_customer(merchant)
    sub = make_subscription(merchant, customer, plan)
    inv = _make_invoice(db, merchant, customer, sub)

    resp = api_client.get(f"/v1/invoices/{inv.id}", headers=_auth(other_token))
    assert resp.status_code == 404


def test_get_invoice_nonexistent_returns_404(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.get("/v1/invoices/99999", headers=_auth(token))
    assert resp.status_code == 404
