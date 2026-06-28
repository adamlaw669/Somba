"""Integration tests for Customers CRUD endpoints."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from somba.db.models import Customer
from tests.conftest import idem_key


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def mut_headers(token: str, key: str | None = None) -> dict:
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": key or idem_key()}


# ---------------------------------------------------------------------------
# POST /v1/customers
# ---------------------------------------------------------------------------


def test_create_customer_returns_201_with_correct_body(api_client, merchant_and_token):
    merchant, token = merchant_and_token
    resp = api_client.post(
        "/v1/customers",
        json={"email": "alice@gym.com", "name": "Alice"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 201
    body = resp.json()["customer"]
    assert body["email"] == "alice@gym.com"
    assert body["name"] == "Alice"
    assert body["merchant_id"] == merchant.id
    assert body["credit_balance"] == 0


def test_create_customer_persists_to_db(api_client, merchant_and_token, db):
    merchant, token = merchant_and_token
    api_client.post(
        "/v1/customers",
        json={"email": "bob@gym.com", "name": "Bob"},
        headers=mut_headers(token),
    )
    customer = db.scalar(
        select(Customer).where(Customer.merchant_id == merchant.id)
    )
    assert customer is not None
    assert customer.email == "bob@gym.com"
    assert customer.name == "Bob"


def test_create_customer_with_external_id(api_client, merchant_and_token, db):
    merchant, token = merchant_and_token
    resp = api_client.post(
        "/v1/customers",
        json={"external_id": "usr_001", "email": "carol@gym.com"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 201
    customer = db.scalar(select(Customer).where(Customer.merchant_id == merchant.id))
    assert customer.external_id == "usr_001"


def test_create_customer_minimal_body_no_email_or_name(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.post(
        "/v1/customers",
        json={},
        headers=mut_headers(token),
    )
    assert resp.status_code == 201
    body = resp.json()["customer"]
    assert body["email"] is None
    assert body["name"] is None


def test_create_customer_requires_auth(api_client):
    resp = api_client.post(
        "/v1/customers",
        json={"email": "x@x.com"},
        headers={"Idempotency-Key": idem_key()},
    )
    assert resp.status_code == 401


def test_create_customer_requires_idempotency_key(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.post(
        "/v1/customers",
        json={"email": "x@x.com"},
        headers=auth(token),
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "missing_idempotency_key"


def test_create_customer_invalid_email_returns_422(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.post(
        "/v1/customers",
        json={"email": "not-an-email"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /v1/customers
# ---------------------------------------------------------------------------


def test_list_customers_returns_all_own_customers(api_client, merchant_and_token, make_customer):
    merchant, token = merchant_and_token
    make_customer(merchant, email="a@gym.com")
    make_customer(merchant, email="b@gym.com")
    make_customer(merchant, email="c@gym.com")

    resp = api_client.get("/v1/customers", headers=auth(token))
    assert resp.status_code == 200
    customers = resp.json()["customers"]
    assert len(customers) == 3
    emails = {c["email"] for c in customers}
    assert emails == {"a@gym.com", "b@gym.com", "c@gym.com"}


def test_list_customers_excludes_other_merchant_customers(
    api_client, merchant_and_token, other_merchant_and_token, make_customer
):
    merchant, token = merchant_and_token
    other_merchant, _ = other_merchant_and_token

    make_customer(merchant, email="mine@gym.com")
    make_customer(other_merchant, email="theirs@gym.com")

    resp = api_client.get("/v1/customers", headers=auth(token))
    customers = resp.json()["customers"]
    assert len(customers) == 1
    assert customers[0]["email"] == "mine@gym.com"


def test_list_customers_empty_when_none_exist(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.get("/v1/customers", headers=auth(token))
    assert resp.status_code == 200
    assert resp.json()["customers"] == []


# ---------------------------------------------------------------------------
# GET /v1/customers/{customer_id}
# ---------------------------------------------------------------------------


def test_get_customer_by_id(api_client, merchant_and_token, make_customer):
    merchant, token = merchant_and_token
    customer = make_customer(merchant, email="dave@gym.com")

    resp = api_client.get(f"/v1/customers/{customer.id}", headers=auth(token))
    assert resp.status_code == 200
    body = resp.json()["customer"]
    assert body["id"] == customer.id
    assert body["email"] == "dave@gym.com"


def test_get_customer_not_found_returns_404(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.get("/v1/customers/99999", headers=auth(token))
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_get_customer_other_merchant_returns_404(
    api_client, merchant_and_token, other_merchant_and_token, make_customer
):
    other_merchant, _ = other_merchant_and_token
    customer = make_customer(other_merchant, email="secret@other.com")

    _, token = merchant_and_token
    resp = api_client.get(f"/v1/customers/{customer.id}", headers=auth(token))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /v1/customers/{customer_id}
# ---------------------------------------------------------------------------


def test_update_customer_name(api_client, merchant_and_token, make_customer, db):
    merchant, token = merchant_and_token
    customer = make_customer(merchant, email="eve@gym.com")

    resp = api_client.patch(
        f"/v1/customers/{customer.id}",
        json={"name": "Eve Updated"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["customer"]["name"] == "Eve Updated"

    db.refresh(customer)
    assert customer.name == "Eve Updated"


def test_update_customer_email(api_client, merchant_and_token, make_customer, db):
    merchant, token = merchant_and_token
    customer = make_customer(merchant, email="old@gym.com")

    resp = api_client.patch(
        f"/v1/customers/{customer.id}",
        json={"email": "new@gym.com"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["customer"]["email"] == "new@gym.com"

    db.refresh(customer)
    assert customer.email == "new@gym.com"


def test_update_customer_external_id(api_client, merchant_and_token, make_customer, db):
    merchant, token = merchant_and_token
    customer = make_customer(merchant)

    resp = api_client.patch(
        f"/v1/customers/{customer.id}",
        json={"external_id": "ext_999"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 200

    db.refresh(customer)
    assert customer.external_id == "ext_999"


def test_update_customer_other_merchant_returns_404(
    api_client, merchant_and_token, other_merchant_and_token, make_customer
):
    other_merchant, _ = other_merchant_and_token
    customer = make_customer(other_merchant)

    _, token = merchant_and_token
    resp = api_client.patch(
        f"/v1/customers/{customer.id}",
        json={"name": "Hijacked"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /v1/customers/{customer_id}
# ---------------------------------------------------------------------------


def test_delete_customer_removes_from_db(api_client, merchant_and_token, make_customer, db):
    merchant, token = merchant_and_token
    customer = make_customer(merchant, email="to-delete@gym.com")
    customer_id = customer.id

    resp = api_client.delete(f"/v1/customers/{customer_id}", headers=mut_headers(token))
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True
    assert resp.json()["id"] == customer_id

    remaining = db.scalar(select(Customer).where(Customer.id == customer_id))
    assert remaining is None


def test_delete_customer_not_found_returns_404(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.delete("/v1/customers/99999", headers=mut_headers(token))
    assert resp.status_code == 404


def test_delete_customer_other_merchant_returns_404(
    api_client, merchant_and_token, other_merchant_and_token, make_customer
):
    other_merchant, _ = other_merchant_and_token
    customer = make_customer(other_merchant)

    _, token = merchant_and_token
    resp = api_client.delete(f"/v1/customers/{customer.id}", headers=mut_headers(token))
    assert resp.status_code == 404
