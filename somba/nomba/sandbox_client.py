"""A deliberately isolated Nomba client for the sandbox test endpoints.

somba.nomba.client caches its auth token in module-level state and reads
credentials from the main NOMBA_CLIENT_ID / NOMBA_CLIENT_SECRET / base URL —
whichever environment (live or sandbox) those happen to point at. Reusing it
here would mean a sandbox test could silently overwrite the cached token a
concurrent real request relies on, or vice versa: a genuine risk once the
account is holding live credentials, which is the whole reason this module
exists.

This module never touches that shared state. It always uses its own
dedicated NOMBA_TEST_CLIENT_ID / NOMBA_TEST_CLIENT_SECRET credentials against
NOMBA_SANDBOX_BASE_URL (defaulting to https://sandbox.nomba.com), issues a
fresh token per call, and shares nothing with the production path.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass


class SandboxNombaError(Exception):
    """Raised when a sandbox call to Nomba fails."""

    def __init__(self, message: str, status_code: int | None = None, body: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def _describe_error(resp) -> str:
    """Pull Nomba's own error description out of the response, if present."""

    try:
        data = resp.json()
        return data.get("description") or data.get("message") or resp.text
    except Exception:
        return resp.text


def _payload_or_raise(resp, action: str) -> dict:
    """Nomba sometimes returns HTTP 200 with a body that still signals
    failure (no "data") instead of a 4xx/5xx — so an HTTP-status-only check
    isn't enough. Check both.

    Nomba's own "status" boolean is not reliable as a success signal — the
    token-issue endpoint sends "status": false even on a genuine success
    (code "00", "Successful", a populated "data"). The one consistent
    signal across endpoints is whether "data" is present, so that's what
    this checks instead.
    """

    try:
        parsed = resp.json()
    except Exception:
        parsed = None

    is_body_error = not isinstance(parsed, dict) or "data" not in parsed
    if resp.is_error or is_body_error:
        description = _describe_error(resp) if parsed is None else (
            parsed.get("description") or parsed.get("message") or resp.text
        )
        raise SandboxNombaError(f"{action}: {description}", resp.status_code, resp.text)
    return parsed["data"]


def _sandbox_base_url() -> str:
    return os.environ.get("NOMBA_SANDBOX_BASE_URL", "https://sandbox.nomba.com")


def _test_client_id() -> str:
    return os.environ.get("NOMBA_TEST_CLIENT_ID", "")


def _test_client_secret() -> str:
    return os.environ.get("NOMBA_TEST_CLIENT_SECRET", "")


def _parent_account_id() -> str:
    return os.environ.get("NOMBA_PARENT_ACCOUNT_ID") or os.environ.get("NOMBA_ACCOUNT_ID", "")


def _sub_account_id() -> str:
    return os.environ.get("NOMBA_ACCOUNT_ID", "")


def sandbox_issue_token() -> str:
    """Issue a fresh sandbox access token. Never cached, never shared."""

    import httpx

    base_url = _sandbox_base_url()
    client_id = _test_client_id()
    client_secret = _test_client_secret()

    if not client_id or not client_secret:
        raise SandboxNombaError(
            "NOMBA_TEST_CLIENT_ID / NOMBA_TEST_CLIENT_SECRET are not configured"
        )

    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{base_url}/v1/auth/token/issue",
            json={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
            headers={"accountId": _parent_account_id(), "Content-Type": "application/json"},
        )
    data = _payload_or_raise(resp, "Sandbox auth failed")
    return data["access_token"]


@dataclass
class SandboxVirtualAccountResult:
    account_number: str
    bank_name: str
    account_holder_id: str
    account_ref: str


def sandbox_create_virtual_account(*, customer_name: str) -> SandboxVirtualAccountResult:
    """Create a virtual account against the sandbox environment only."""

    import httpx

    base_url = _sandbox_base_url()
    token = sandbox_issue_token()
    sub_account_id = _sub_account_id()
    account_ref = f"sandbox-va-{uuid.uuid4().hex}"

    headers = {
        "Authorization": f"Bearer {token}",
        "accountId": _parent_account_id(),
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{base_url}/v1/accounts/virtual/{sub_account_id}",
            json={"accountRef": account_ref, "accountName": customer_name},
            headers=headers,
        )
    data = _payload_or_raise(resp, "Sandbox virtual account creation failed")
    return SandboxVirtualAccountResult(
        account_number=data["bankAccountNumber"],
        bank_name=data.get("bankName", ""),
        account_holder_id=data.get("accountHolderId", ""),
        account_ref=data.get("accountRef", account_ref),
    )
