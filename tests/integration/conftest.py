"""Integration-test fixtures: real HTTP client against in-memory DB."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from somba.api.app import app
from somba.db.session import get_db


@pytest.fixture(scope="function")
def api_client(db):
    """FastAPI test client wired to the function-scoped in-memory DB."""

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def merchant_and_token(make_merchant):
    return make_merchant("Gym Merchant")


@pytest.fixture
def other_merchant_and_token(make_merchant):
    return make_merchant("Other Merchant")
