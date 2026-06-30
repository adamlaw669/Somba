"""Nomba HTTP client: auth, virtual accounts, direct debits, transactions."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

log = logging.getLogger(__name__)

_TOKEN_REFRESH_BUFFER = 60  # seconds before expiry to proactively refresh


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


@dataclass
class MandateResult:
    mandate_id: str
    merchant_reference: str
    description: str


@dataclass
class MandateStatus:
    mandate_id: str
    status: str            # ACTIVE | SUSPENDED | DELETED
    advice_status: str     # ADVICE_NOT_SENT | ADVICE_SENT

    @property
    def is_debitable(self) -> bool:
        return self.status.upper() == "ACTIVE" and self.advice_status.upper() == "ADVICE_SENT"


# ---------------------------------------------------------------------------
# Auth token management
# ---------------------------------------------------------------------------

@dataclass
class _TokenState:
    access_token: str
    refresh_token: str
    expires_at: datetime


_state: _TokenState | None = None


def _base_url() -> str:
    return os.environ.get("NOMBA_API_BASE_URL", "https://api.nomba.com")


def _account_id() -> str:
    return os.environ.get("NOMBA_ACCOUNT_ID", "")


def _get_token(base_url: str | None = None) -> str:
    global _state
    url = base_url or _base_url()
    now = datetime.now(timezone.utc)

    if _state is not None:
        remaining = (_state.expires_at - now).total_seconds()
        if remaining > _TOKEN_REFRESH_BUFFER:
            return _state.access_token
        # Attempt refresh before falling through to full re-issue
        try:
            return _refresh(url, _state.refresh_token)
        except Exception as exc:
            log.warning("nomba: token refresh failed, re-issuing: %s", exc)

    return _issue(url)


def _issue(base_url: str) -> str:
    global _state
    import httpx

    client_id = os.environ.get("NOMBA_CLIENT_ID", "")
    client_secret = os.environ.get("NOMBA_CLIENT_SECRET", "")

    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{base_url}/v1/auth/token/issue",
            json={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
            headers={"accountId": _account_id(), "Content-Type": "application/json"},
        )
    resp.raise_for_status()
    data = resp.json()["data"]
    _state = _TokenState(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 1800)),
    )
    return _state.access_token


def _refresh(base_url: str, refresh_token: str) -> str:
    global _state
    import httpx

    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{base_url}/v1/auth/token/refresh",
            json={"refresh_token": refresh_token},
            headers={"accountId": _account_id(), "Content-Type": "application/json"},
        )
    resp.raise_for_status()
    data = resp.json()["data"]
    _state = _TokenState(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 1800)),
    )
    return _state.access_token


def _headers(base_url: str | None = None) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_token(base_url)}",
        "accountId": _account_id(),
        "Content-Type": "application/json",
    }


def _numeric_reference() -> str:
    """Generate a numeric-only merchant reference (Nomba requirement)."""
    # Use millisecond epoch; take last 17 digits for uniqueness without overflow
    return str(int(time.time() * 1000))[-17:]


# ---------------------------------------------------------------------------
# Virtual accounts
# ---------------------------------------------------------------------------


def create_virtual_account(
    *,
    customer_name: str,
    base_url: str | None = None,
) -> str:
    """Create a virtual account and return the bank account number."""
    url = base_url or _base_url()
    import httpx

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{url}/v1/accounts/virtual",
            json={"accountName": customer_name},
            headers=_headers(url),
        )
    resp.raise_for_status()
    body = resp.json()
    return body["data"]["bankAccountNumber"]


# ---------------------------------------------------------------------------
# Direct Debit
# ---------------------------------------------------------------------------


def create_mandate(
    *,
    customer_account_number: str,
    bank_code: str,
    customer_name: str,
    customer_address: str,
    customer_email: str,
    customer_phone: str,
    narration: str,
    start_date: str,   # ISO-like: "2025-08-29T15:30"
    end_date: str,
    base_url: str | None = None,
) -> MandateResult:
    """Create a direct debit mandate. Customer must complete N50 verification."""
    url = base_url or _base_url()
    import httpx

    merchant_reference = _numeric_reference()

    payload: dict[str, Any] = {
        "customerAccountNumber": customer_account_number,
        "bankCode": bank_code,
        "customerName": customer_name,
        "customerAddress": customer_address,
        "customerAccountName": customer_name,
        "frequency": "VARIABLE",
        "narration": narration,
        "customerPhoneNumber": customer_phone,
        "merchantReference": merchant_reference,
        "startDate": start_date,
        "endDate": end_date,
        "customerEmail": customer_email,
        "startImmediately": True,
    }

    with httpx.Client(timeout=30) as client:
        resp = client.post(f"{url}/v1/direct-debits", json=payload, headers=_headers(url))
    resp.raise_for_status()
    body = resp.json()
    data = body["data"]

    return MandateResult(
        mandate_id=data["mandateId"],
        merchant_reference=data.get("merchantReference", merchant_reference),
        description=data.get("description", ""),
    )


def check_mandate_status(
    *,
    mandate_id: str,
    base_url: str | None = None,
) -> MandateStatus:
    """Check current mandate status."""
    url = base_url or _base_url()
    import httpx

    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{url}/v1/direct-debits/status",
            params={"mandateId": mandate_id},
            headers=_headers(url),
        )
    resp.raise_for_status()
    data = resp.json()["data"]

    return MandateStatus(
        mandate_id=data.get("mandateId", mandate_id),
        status=data.get("mandateStatus", ""),
        advice_status=data.get("mandateAdviceStatus", ""),
    )


def debit_mandate(
    *,
    mandate_id: str,
    amount_kobo: int,
    base_url: str | None = None,
) -> NombaChargeResult:
    """Initiate a direct debit pull against an active mandate.

    amount_kobo is converted to naira (÷ 100) before sending because
    Nomba expects naira with two decimal places.
    """
    url = base_url or _base_url()
    amount_naira = f"{amount_kobo / 100:.2f}"

    try:
        import httpx

        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{url}/v1/direct-debits/debit-mandate",
                json={"mandateId": mandate_id, "amount": amount_naira},
                headers=_headers(url),
            )
        body: dict[str, Any] = resp.json()
    except Exception as exc:
        log.warning("nomba.debit_mandate: network error mandate=%s: %s", mandate_id, exc)
        return NombaChargeResult(
            status=NombaChargeStatus.uncertain,
            transaction_id=None,
            failure_reason=f"network_error: {exc}",
            response_code=None,
            raw={},
        )

    return _parse_debit_response(body, mandate_id)


def _parse_debit_response(body: dict[str, Any], mandate_id: str) -> NombaChargeResult:
    code: str = str(body.get("code", ""))
    data: dict[str, Any] = body.get("data") or {}
    txn_status: str = (data.get("status") or "").upper()
    message: str = data.get("message") or body.get("description", "")

    if code == "00" and txn_status == "SUCCESS":
        return NombaChargeResult(
            status=NombaChargeStatus.succeeded,
            transaction_id=f"dd_{mandate_id}",
            failure_reason=None,
            response_code="00",
            raw=body,
        )

    return NombaChargeResult(
        status=NombaChargeStatus.failed,
        transaction_id=None,
        failure_reason=message or f"code={code}",
        response_code=code,
        raw=body,
    )


# ---------------------------------------------------------------------------
# Transaction verification
# ---------------------------------------------------------------------------


def verify_transaction(
    *,
    order_reference: str,
    base_url: str | None = None,
) -> NombaChargeResult:
    """Fetch the definitive status of a transaction by order reference."""
    url = base_url or _base_url()

    try:
        import httpx

        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{url}/v1/transactions/accounts/single",
                params={"orderReference": order_reference},
                headers=_headers(url),
            )
        body: dict[str, Any] = resp.json()
    except Exception as exc:
        log.warning("nomba.verify: network error order=%s: %s", order_reference, exc)
        return NombaChargeResult(
            status=NombaChargeStatus.uncertain,
            transaction_id=None,
            failure_reason=f"network_error: {exc}",
            response_code=None,
            raw={},
        )

    code: str = str(body.get("code", ""))
    data: dict[str, Any] = body.get("data") or {}
    txn_status: str = (data.get("status") or "").upper()
    transaction_id: str | None = data.get("transactionId") or data.get("id")

    if code == "00" and txn_status == "SUCCESS":
        return NombaChargeResult(
            status=NombaChargeStatus.succeeded,
            transaction_id=transaction_id,
            failure_reason=None,
            response_code="00",
            raw=body,
        )

    return NombaChargeResult(
        status=NombaChargeStatus.failed,
        transaction_id=transaction_id,
        failure_reason=data.get("reason") or body.get("description"),
        response_code=code,
        raw=body,
    )


# ---------------------------------------------------------------------------
# Account transaction sweep
# ---------------------------------------------------------------------------


def fetch_account_transactions(
    *,
    from_dt: datetime,
    to_dt: datetime,
    base_url: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch settled account transactions for reconciliation sweep."""
    url = base_url or _base_url()

    params = {
        "dateFrom": from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dateTo": to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    try:
        import httpx

        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{url}/v1/transactions/accounts",
                params=params,
                headers=_headers(url),
            )
        body: dict[str, Any] = resp.json()
        return (body.get("data") or {}).get("results", [])
    except Exception as exc:
        log.warning("nomba.fetch_transactions: network error: %s", exc)
        return []
