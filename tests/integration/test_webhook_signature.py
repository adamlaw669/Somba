"""Outbound webhook signing: the emitter signs each event body with HMAC-SHA256
using the merchant's own webhook secret, so a merchant can verify authenticity."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone

from somba.db.models import OutboxEvent, OutboxEventStatus
from somba.workers.emitter.emitter import _build_body, _sign

NOW = datetime(2026, 6, 30, 12, 0, 0, tzinfo=timezone.utc)


def _merchant_verify(secret: str, body: dict, signature: str) -> bool:
    """What a merchant does on their end to authenticate the webhook."""
    canonical = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
    expected = hmac.new(secret.encode(), canonical, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def test_merchant_can_verify_signature_with_secret(db, merchant_and_token):
    merchant, _ = merchant_and_token
    secret = merchant.webhook_secret

    event = OutboxEvent(
        merchant_id=merchant.id,
        aggregate_type="subscription",
        aggregate_id="1",
        event_type="charge.succeeded",
        payload={"subscription_id": 1, "amount": 5000},
        partition_key="1",
        status=OutboxEventStatus.pending,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    body = _build_body(event, NOW)
    signature = _sign(secret, body)

    # A merchant holding the shared secret can reproduce and verify the signature.
    assert _merchant_verify(secret, body, signature)


def test_wrong_secret_fails_verification(db, merchant_and_token):
    merchant, _ = merchant_and_token

    event = OutboxEvent(
        merchant_id=merchant.id,
        aggregate_type="subscription",
        aggregate_id="1",
        event_type="charge.succeeded",
        payload={"subscription_id": 1, "amount": 5000},
        partition_key="1",
        status=OutboxEventStatus.pending,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    body = _build_body(event, NOW)
    signature = _sign(merchant.webhook_secret, body)

    # An attacker without the real secret cannot verify.
    assert not _merchant_verify("wrong-secret", body, signature)
