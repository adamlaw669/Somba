"""Nomba account-scoping: token issue/refresh must authenticate with the
PARENT account, while resource calls (debits, VAs, verify) must be scoped
to the SUB-account -- per Nomba's onboarding instructions. Mixing these up
either fails auth outright or attributes calls to the wrong account."""

from __future__ import annotations

import pytest

from somba.nomba import client


class _FakeResponse:
    def __init__(self, data: dict) -> None:
        self._data = data

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._data


class _FakeHTTPXClient:
    """Captures the headers/json of the last POST for assertions."""

    last_headers: dict | None = None
    last_json: dict | None = None
    last_url: str | None = None

    def __init__(self, timeout=None) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url, json=None, headers=None, **kwargs):
        _FakeHTTPXClient.last_url = url
        _FakeHTTPXClient.last_json = json
        _FakeHTTPXClient.last_headers = headers
        return _FakeResponse({
            "data": {
                "access_token": "tok-1",
                "refresh_token": "refresh-1",
                "expires_in": 1800,
            }
        })


@pytest.fixture(autouse=True)
def _reset_token_state(monkeypatch):
    monkeypatch.setattr(client, "_state", None)
    monkeypatch.setattr("httpx.Client", _FakeHTTPXClient)
    yield


def test_issue_authenticates_with_parent_account_id(monkeypatch):
    monkeypatch.setenv("NOMBA_PARENT_ACCOUNT_ID", "parent-123")
    monkeypatch.setenv("NOMBA_ACCOUNT_ID", "sub-456")

    client._issue("https://api.test")

    assert _FakeHTTPXClient.last_headers["accountId"] == "parent-123"


def test_refresh_authenticates_with_parent_account_id(monkeypatch):
    monkeypatch.setenv("NOMBA_PARENT_ACCOUNT_ID", "parent-123")
    monkeypatch.setenv("NOMBA_ACCOUNT_ID", "sub-456")

    client._refresh("https://api.test", "some-refresh-token")

    assert _FakeHTTPXClient.last_headers["accountId"] == "parent-123"


def test_resource_headers_scope_to_sub_account(monkeypatch):
    monkeypatch.setenv("NOMBA_PARENT_ACCOUNT_ID", "parent-123")
    monkeypatch.setenv("NOMBA_ACCOUNT_ID", "sub-456")

    headers = client._headers("https://api.test")

    assert headers["accountId"] == "sub-456"


def test_parent_account_id_falls_back_to_sub_account_when_unset(monkeypatch):
    monkeypatch.delenv("NOMBA_PARENT_ACCOUNT_ID", raising=False)
    monkeypatch.setenv("NOMBA_ACCOUNT_ID", "only-account-789")

    client._issue("https://api.test")

    assert _FakeHTTPXClient.last_headers["accountId"] == "only-account-789"


# ---------------------------------------------------------------------------
# Virtual account creation: confirmed live against the real Nomba API that a
# bare sub-account-scoped call 403s -- VA creation for a sub-account is a
# PARENT-account operation against /v1/accounts/virtual/{subAccountId}.
# ---------------------------------------------------------------------------


class _FakeVAClient:
    last_url: str | None = None
    last_json: dict | None = None
    last_headers: dict | None = None

    def __init__(self, timeout=None) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url, json=None, headers=None, **kwargs):
        _FakeVAClient.last_url = url
        _FakeVAClient.last_json = json
        _FakeVAClient.last_headers = headers
        return _FakeResponse({
            "code": "00",
            "data": {
                "bankAccountNumber": "7817594582",
                "bankName": "Nombank MFB",
                "accountHolderId": "holder-123",
                "accountRef": json["accountRef"],
            },
        })


def test_create_virtual_account_targets_sub_account_path_with_parent_header(monkeypatch):
    from datetime import datetime, timedelta, timezone

    from somba.nomba.client import _TokenState

    monkeypatch.setenv("NOMBA_PARENT_ACCOUNT_ID", "parent-123")
    monkeypatch.setenv("NOMBA_ACCOUNT_ID", "sub-456")
    # Pre-seed a valid token so create_virtual_account's own POST is the only
    # request the fake client needs to shape a response for.
    monkeypatch.setattr(client, "_state", _TokenState(
        access_token="tok", refresh_token="r",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    ))
    monkeypatch.setattr("httpx.Client", _FakeVAClient)

    result = client.create_virtual_account(customer_name="Test Customer", base_url="https://api.test")

    assert _FakeVAClient.last_url == "https://api.test/v1/accounts/virtual/sub-456"
    assert _FakeVAClient.last_headers["accountId"] == "parent-123"
    assert len(_FakeVAClient.last_json["accountRef"]) >= 16
    assert result.account_number == "7817594582"
    assert result.bank_name == "Nombank MFB"
    assert result.account_holder_id == "holder-123"
