"""Nomba webhook signature verification."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Any


def verify_nomba_signature(payload: dict[str, Any], nomba_timestamp: str, nomba_signature: str) -> bool:
    secret = os.environ.get("WEBHOOK_SIGNING_SECRET", "")
    if not secret:
        return False

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
        nomba_timestamp,
    ])

    digest = hmac.new(secret.encode(), hashing_payload.encode(), hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected.lower(), nomba_signature.lower())
