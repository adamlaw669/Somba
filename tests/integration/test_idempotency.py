"""Idempotency end-to-end: a repeated Idempotency-Key replays the stored
response instead of performing the action twice."""

from __future__ import annotations

from sqlalchemy import func, select

from somba.db.models import Customer


def _headers(token: str, key: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": key}


def _customer_count(db) -> int:
    return db.scalar(select(func.count()).select_from(Customer))


def test_same_key_same_body_replays_response(api_client, merchant_and_token, db):
    _, token = merchant_and_token
    key = "idem-fixed-123"
    body = {"email": "alice@gym.com", "name": "Alice"}

    first = api_client.post("/v1/customers", json=body, headers=_headers(token, key))
    assert first.status_code == 201
    assert "Idempotency-Replayed" not in first.headers

    second = api_client.post("/v1/customers", json=body, headers=_headers(token, key))
    assert second.status_code == 201
    assert second.headers.get("Idempotency-Replayed") == "true"

    # Identical response, and only ONE customer was actually created.
    assert second.json() == first.json()
    assert _customer_count(db) == 1


def test_same_key_different_body_conflicts(api_client, merchant_and_token, db):
    _, token = merchant_and_token
    key = "idem-fixed-456"

    first = api_client.post(
        "/v1/customers", json={"email": "a@gym.com", "name": "A"}, headers=_headers(token, key)
    )
    assert first.status_code == 201

    second = api_client.post(
        "/v1/customers", json={"email": "different@gym.com", "name": "B"}, headers=_headers(token, key)
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "idempotency_key_reuse"
    assert _customer_count(db) == 1  # the conflicting request created nothing


def test_different_key_creates_distinct_resources(api_client, merchant_and_token, db):
    _, token = merchant_and_token
    body = {"email": "a@gym.com", "name": "A"}

    api_client.post("/v1/customers", json=body, headers=_headers(token, "k1"))
    api_client.post("/v1/customers", json={"email": "b@gym.com", "name": "B"}, headers=_headers(token, "k2"))

    assert _customer_count(db) == 2  # distinct keys -> two creations


def test_missing_idempotency_key_rejected(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.post(
        "/v1/customers", json={"email": "x@gym.com"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "missing_idempotency_key"
