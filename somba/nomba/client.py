"""Nomba HTTP client for initiating card/token charges."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

log = logging.getLogger(__name__)

# ISO 8583 / Nomba response-code classifications
_EMPTY_ACCOUNT_CODES = {"51", "61", "65"}
_BROKEN_CARD_CODES = {"14", "54", "55", "57", "58", "62", "89"}
_TRANSIENT_CODES = {"06", "91", "96", "97"}
_RISK_CODES = {"34", "38", "41", "43", "63"}
# codes that leave outcome ambiguous → uncertain
_UNCERTAIN_CODES = {"00", "68"}  # 68 = "response received too late"


class NombaChargeStatus(str, Enum):
    succeeded = "succeeded"
    failed = "failed"
    uncertain = "uncertain"


@dataclass
class NombaChargeResult:
    status: NombaChargeStatus
    transaction_id: str | None
    failure_reason: str | None
    response_code: str | None
    raw: dict[str, Any] = field(default_factory=dict)


def charge(
    *,
    order_reference: str,
    amount_kobo: int,
    customer_token_key: str,
    idempotency_key: str,
    base_url: str | None = None,
) -> NombaChargeResult:
    """Call the Nomba charge endpoint and return a parsed result.

    amount_kobo is converted to naira (÷ 100) before being sent because
    Nomba's API expects naira, not kobo.
    """
    base_url = base_url or os.environ.get("NOMBA_API_BASE_URL", "https://api.nomba.com")
    token = os.environ.get("NOMBA_API_TOKEN", "")

    payload: dict[str, Any] = {
        "amount": amount_kobo / 100,
        "customerTokenKey": customer_token_key,
        "orderReference": order_reference,
        "idempotencyKey": idempotency_key,
        "description": "Somba subscription charge",
    }

    try:
        import httpx

        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{base_url}/api/v1/charges",
                json=payload,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
        body: dict[str, Any] = resp.json()
    except Exception as exc:
        log.warning("nomba.charge: network error order=%s: %s", order_reference, exc)
        return NombaChargeResult(
            status=NombaChargeStatus.uncertain,
            transaction_id=None,
            failure_reason=f"network_error: {exc}",
            response_code=None,
            raw={},
        )

    return _parse_response(body, order_reference)


def _parse_response(body: dict[str, Any], order_reference: str) -> NombaChargeResult:
    request_ok: bool = body.get("requestSuccessful", False)
    top_code: str = str(body.get("responseCode", ""))
    response_body: dict[str, Any] = body.get("responseBody") or {}
    txn_code: str = str(response_body.get("responseCode", top_code))
    transaction_id: str | None = response_body.get("transactionId") or response_body.get("sessionId")
    failure_reason: str | None = body.get("responseMessage") or response_body.get("responseMessage")

    effective_code = txn_code or top_code

    if request_ok and effective_code == "00":
        return NombaChargeResult(
            status=NombaChargeStatus.succeeded,
            transaction_id=transaction_id,
            failure_reason=None,
            response_code="00",
            raw=body,
        )

    if effective_code in _UNCERTAIN_CODES and not request_ok:
        return NombaChargeResult(
            status=NombaChargeStatus.uncertain,
            transaction_id=transaction_id,
            failure_reason=failure_reason,
            response_code=effective_code,
            raw=body,
        )

    return NombaChargeResult(
        status=NombaChargeStatus.failed,
        transaction_id=transaction_id,
        failure_reason=failure_reason,
        response_code=effective_code,
        raw=body,
    )
