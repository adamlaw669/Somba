"""Merchant isolation: a merchant can never read another merchant's resources.

Customers and subscriptions are covered in their own API test files; this closes
the suite with plans and invoices, so all four core resources return 404 when
fetched with the wrong merchant's key.
"""

from __future__ import annotations

from datetime import datetime, timezone

from somba.db.models import Invoice, InvoiceStatus, InvoiceType, SubscriptionStatus

NOW = datetime(2026, 6, 30, 12, 0, 0, tzinfo=timezone.utc)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_get_plan_other_merchant_returns_404(
    api_client, merchant_and_token, other_merchant_and_token, make_plan
):
    _, token = merchant_and_token
    other_merchant, _ = other_merchant_and_token
    their_plan = make_plan(other_merchant, name="Secret Plan")

    resp = api_client.get(f"/v1/plans/{their_plan.id}", headers=_auth(token))

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_get_invoice_other_merchant_returns_404(
    api_client, merchant_and_token, other_merchant_and_token,
    make_plan, make_customer, make_subscription, db,
):
    _, token = merchant_and_token
    other_merchant, _ = other_merchant_and_token

    plan = make_plan(other_merchant)
    customer = make_customer(other_merchant, email="theirs@gym.com")
    sub = make_subscription(other_merchant, customer, plan, status=SubscriptionStatus.active)
    their_invoice = Invoice(
        merchant_id=other_merchant.id,
        subscription_id=sub.id,
        customer_id=customer.id,
        amount=10_000,
        status=InvoiceStatus.open,
        type=InvoiceType.regular,
        period_start=NOW,
        period_end=NOW,
    )
    db.add(their_invoice)
    db.commit()
    db.refresh(their_invoice)

    resp = api_client.get(f"/v1/invoices/{their_invoice.id}", headers=_auth(token))

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_list_plans_excludes_other_merchant(
    api_client, merchant_and_token, other_merchant_and_token, make_plan
):
    _, token = merchant_and_token
    other_merchant, _ = other_merchant_and_token
    make_plan(other_merchant, name="Theirs")

    resp = api_client.get("/v1/plans", headers=_auth(token))

    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()["plans"]]
    assert "Theirs" not in names


def test_list_invoices_excludes_other_merchant(
    api_client, merchant_and_token, other_merchant_and_token,
    make_plan, make_customer, make_subscription, db,
):
    _, token = merchant_and_token
    other_merchant, _ = other_merchant_and_token

    plan = make_plan(other_merchant)
    customer = make_customer(other_merchant, email="theirs2@gym.com")
    sub = make_subscription(other_merchant, customer, plan, status=SubscriptionStatus.active)
    db.add(Invoice(
        merchant_id=other_merchant.id,
        subscription_id=sub.id,
        customer_id=customer.id,
        amount=10_000,
        status=InvoiceStatus.open,
        type=InvoiceType.regular,
        period_start=NOW,
        period_end=NOW,
    ))
    db.commit()

    resp = api_client.get("/v1/invoices", headers=_auth(token))

    assert resp.status_code == 200
    assert resp.json()["invoices"] == []
