"""Integration tests for GET /v1/events and POST /v1/events/:id/replay."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from somba.db.models import OutboxEvent, OutboxEventStatus, WebhookDelivery, WebhookDeliveryStatus


def _idem() -> str:
    return uuid.uuid4().hex


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": _idem()}


def _make_event(db, merchant, *, event_type="charge.succeeded", status=OutboxEventStatus.pending):
    event = OutboxEvent(
        merchant_id=merchant.id,
        aggregate_type="subscription",
        aggregate_id="1",
        event_type=event_type,
        payload={"subscription_id": 1},
        partition_key="1",
        status=status,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


# ---------------------------------------------------------------------------
# List events
# ---------------------------------------------------------------------------


def test_list_events_returns_merchant_events(
    api_client, merchant_and_token, db
):
    merchant, token = merchant_and_token
    event = _make_event(db, merchant)

    resp = api_client.get("/v1/events", headers=_auth(token))
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()["events"]]
    assert event.id in ids


def test_list_events_scoped_to_merchant(
    api_client, merchant_and_token, other_merchant_and_token, db
):
    merchant, token = merchant_and_token
    other_merchant, other_token = other_merchant_and_token

    event = _make_event(db, merchant)

    resp = api_client.get("/v1/events", headers=_auth(other_token))
    ids = [e["id"] for e in resp.json()["events"]]
    assert event.id not in ids


def test_list_events_filter_by_event_type(
    api_client, merchant_and_token, db
):
    merchant, token = merchant_and_token
    e1 = _make_event(db, merchant, event_type="charge.succeeded")
    e2 = _make_event(db, merchant, event_type="charge.failed")

    resp = api_client.get("/v1/events?event_type=charge.succeeded", headers=_auth(token))
    ids = [e["id"] for e in resp.json()["events"]]
    assert e1.id in ids
    assert e2.id not in ids


def test_list_events_filter_by_status(
    api_client, merchant_and_token, db
):
    merchant, token = merchant_and_token
    pending = _make_event(db, merchant, status=OutboxEventStatus.pending)
    published = _make_event(db, merchant, status=OutboxEventStatus.published)

    resp = api_client.get("/v1/events?status=published", headers=_auth(token))
    ids = [e["id"] for e in resp.json()["events"]]
    assert published.id in ids
    assert pending.id not in ids


def test_list_events_invalid_status_returns_400(
    api_client, merchant_and_token
):
    _, token = merchant_and_token
    resp = api_client.get("/v1/events?status=unknown", headers=_auth(token))
    assert resp.status_code == 400


def test_list_events_unauthenticated_returns_401(api_client):
    resp = api_client.get("/v1/events", headers={"Idempotency-Key": _idem()})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------


def test_replay_resets_published_event_to_pending(
    api_client, merchant_and_token, db
):
    merchant, token = merchant_and_token
    event = _make_event(db, merchant, status=OutboxEventStatus.published)

    resp = api_client.post(f"/v1/events/{event.id}/replay", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["replayed"] is True

    db.refresh(event)
    assert event.status == OutboxEventStatus.pending


def test_replay_resets_delivery_record(
    api_client, merchant_and_token, db
):
    merchant, token = merchant_and_token
    event = _make_event(db, merchant, status=OutboxEventStatus.published)

    delivery = WebhookDelivery(
        merchant_id=merchant.id,
        outbox_event_id=event.id,
        event_type=event.event_type,
        payload={},
        signature="abc",
        status=WebhookDeliveryStatus.failed,
        attempt_count=3,
    )
    db.add(delivery)
    db.commit()

    api_client.post(f"/v1/events/{event.id}/replay", headers=_auth(token))

    db.refresh(delivery)
    assert delivery.status == WebhookDeliveryStatus.pending
    assert delivery.attempt_count == 0
    assert delivery.next_retry_at is None


def test_replay_cross_merchant_returns_404(
    api_client, merchant_and_token, other_merchant_and_token, db
):
    merchant, token = merchant_and_token
    other_merchant, other_token = other_merchant_and_token

    event = _make_event(db, merchant)

    resp = api_client.post(f"/v1/events/{event.id}/replay", headers=_auth(other_token))
    assert resp.status_code == 404


def test_replay_nonexistent_returns_404(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.post("/v1/events/99999/replay", headers=_auth(token))
    assert resp.status_code == 404
