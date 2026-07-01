"""Nomba inbound webhook HMAC verification: a valid signature is accepted,
any tampering is rejected with 401."""

from __future__ import annotations

import base64
import hashlib
import hmac


def _sign_nomba(payload: dict, timestamp: str, secret: str) -> str:
    """Reproduce Nomba's signing exactly as somba.nomba.intake verifies it."""
    data = payload.get("data", {})
    merchant = data.get("merchant", {})
    transaction = data.get("transaction", {})

    response_code = transaction.get("responseCode") or ""
    if response_code == "null":
        response_code = ""

    hashing_payload = ":".join([
        payload.get("event_type", ""),
        payload.get("requestId", ""),
        merchant.get("userId", ""),
        merchant.get("walletId", ""),
        transaction.get("transactionId", ""),
        transaction.get("type", ""),
        transaction.get("time", ""),
        response_code,
        timestamp,
    ])
    digest = hmac.new(secret.encode(), hashing_payload.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def _payload() -> dict:
    return {
        "event_type": "payment_failed",  # non-settlement path: just acks
        "requestId": "req_1",
        "data": {
            "merchant": {"userId": "u1", "walletId": "w1"},
            "transaction": {
                "transactionId": "t1",
                "type": "debit",
                "time": "2026-06-30T00:00:00Z",
                "responseCode": "00",
            },
        },
    }


SECRET = "test-signing-secret"
TS = "1700000000"


def test_valid_signature_accepted(api_client, monkeypatch):
    monkeypatch.setenv("WEBHOOK_SIGNING_SECRET", SECRET)
    payload = _payload()
    sig = _sign_nomba(payload, TS, SECRET)

    resp = api_client.post(
        "/v1/webhooks/nomba",
        json=payload,
        headers={"nomba-timestamp": TS, "nomba-signature": sig},
    )

    assert resp.status_code == 200
    assert resp.json() == {"received": True}


def test_tampered_payload_rejected(api_client, monkeypatch):
    monkeypatch.setenv("WEBHOOK_SIGNING_SECRET", SECRET)
    payload = _payload()
    sig = _sign_nomba(payload, TS, SECRET)

    # Tamper AFTER signing — the signature no longer matches the body.
    payload["data"]["transaction"]["transactionId"] = "TAMPERED"

    resp = api_client.post(
        "/v1/webhooks/nomba",
        json=payload,
        headers={"nomba-timestamp": TS, "nomba-signature": sig},
    )

    assert resp.status_code == 401
    assert resp.json() == {"error": "invalid_signature"}


def test_wrong_secret_rejected(api_client, monkeypatch):
    monkeypatch.setenv("WEBHOOK_SIGNING_SECRET", SECRET)
    payload = _payload()
    sig = _sign_nomba(payload, TS, "attacker-secret")  # signed with the wrong key

    resp = api_client.post(
        "/v1/webhooks/nomba",
        json=payload,
        headers={"nomba-timestamp": TS, "nomba-signature": sig},
    )

    assert resp.status_code == 401
