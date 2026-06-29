"""Integration tests for Plans CRUD endpoints.

Every test drives real HTTP requests through the FastAPI app against an
in-memory SQLite database. Assertions cover both HTTP responses and the
actual database state.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from somba.db.models import Plan, PlanStatus
from tests.conftest import idem_key


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def mut_headers(token: str, key: str | None = None) -> dict:
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": key or idem_key()}


# ---------------------------------------------------------------------------
# POST /v1/plans
# ---------------------------------------------------------------------------


def test_create_plan_returns_201_with_correct_body(api_client, merchant_and_token):
    merchant, token = merchant_and_token
    resp = api_client.post(
        "/v1/plans",
        json={"name": "Monthly Basic", "amount": 5000, "interval": "month"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 201
    body = resp.json()["plan"]
    assert body["name"] == "Monthly Basic"
    assert body["amount"] == 5000
    assert body["currency"] == "NGN"
    assert body["interval"] == "month"
    assert body["interval_count"] == 1
    assert body["trial_days"] == 0
    assert body["status"] == "active"
    assert body["merchant_id"] == merchant.id


def test_create_plan_persists_to_db(api_client, merchant_and_token, db):
    merchant, token = merchant_and_token
    api_client.post(
        "/v1/plans",
        json={"name": "Annual", "amount": 50000, "interval": "year"},
        headers=mut_headers(token),
    )
    plan = db.scalar(select(Plan).where(Plan.merchant_id == merchant.id))
    assert plan is not None
    assert plan.name == "Annual"
    assert plan.amount == 50000
    assert plan.status == PlanStatus.active


def test_create_plan_requires_bearer_token(api_client):
    resp = api_client.post(
        "/v1/plans",
        json={"name": "X", "amount": 100, "interval": "month"},
        headers={"Idempotency-Key": idem_key()},
    )
    assert resp.status_code == 401


def test_create_plan_requires_idempotency_key(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.post(
        "/v1/plans",
        json={"name": "X", "amount": 100, "interval": "month"},
        headers=auth(token),
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "missing_idempotency_key"


def test_create_plan_invalid_interval_returns_422(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.post(
        "/v1/plans",
        json={"name": "X", "amount": 100, "interval": "biweekly"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 422


def test_create_plan_zero_amount_returns_422(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.post(
        "/v1/plans",
        json={"name": "Free", "amount": 0, "interval": "month"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 422


def test_create_plan_custom_currency_and_interval_count(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.post(
        "/v1/plans",
        json={"name": "Bi-weekly", "amount": 2500, "interval": "week", "interval_count": 2, "currency": "USD"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 201
    body = resp.json()["plan"]
    assert body["interval"] == "week"
    assert body["interval_count"] == 2
    assert body["currency"] == "USD"


# ---------------------------------------------------------------------------
# GET /v1/plans
# ---------------------------------------------------------------------------


def test_list_plans_returns_all_own_plans(api_client, merchant_and_token, make_plan):
    merchant, token = merchant_and_token
    make_plan(merchant, name="Plan A")
    make_plan(merchant, name="Plan B")
    make_plan(merchant, name="Plan C")

    resp = api_client.get("/v1/plans", headers=auth(token))
    assert resp.status_code == 200
    plans = resp.json()["plans"]
    assert len(plans) == 3
    names = {p["name"] for p in plans}
    assert names == {"Plan A", "Plan B", "Plan C"}


def test_list_plans_excludes_other_merchant_plans(
    api_client, merchant_and_token, other_merchant_and_token, make_plan
):
    merchant, token = merchant_and_token
    other_merchant, _ = other_merchant_and_token

    make_plan(merchant, name="My Plan")
    make_plan(other_merchant, name="Their Plan")

    resp = api_client.get("/v1/plans", headers=auth(token))
    plans = resp.json()["plans"]
    assert len(plans) == 1
    assert plans[0]["name"] == "My Plan"


def test_list_plans_returns_empty_list_when_none_exist(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.get("/v1/plans", headers=auth(token))
    assert resp.status_code == 200
    assert resp.json()["plans"] == []


# ---------------------------------------------------------------------------
# GET /v1/plans/{plan_id}
# ---------------------------------------------------------------------------


def test_get_plan_by_id(api_client, merchant_and_token, make_plan):
    merchant, token = merchant_and_token
    plan = make_plan(merchant, name="Specific Plan", amount=7500)

    resp = api_client.get(f"/v1/plans/{plan.id}", headers=auth(token))
    assert resp.status_code == 200
    body = resp.json()["plan"]
    assert body["id"] == plan.id
    assert body["name"] == "Specific Plan"
    assert body["amount"] == 7500


def test_get_plan_not_found_returns_404(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.get("/v1/plans/99999", headers=auth(token))
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_get_plan_other_merchant_returns_404(
    api_client, merchant_and_token, other_merchant_and_token, make_plan
):
    other_merchant, _ = other_merchant_and_token
    plan = make_plan(other_merchant, name="Not Mine")

    _, token = merchant_and_token
    resp = api_client.get(f"/v1/plans/{plan.id}", headers=auth(token))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /v1/plans/{plan_id}
# ---------------------------------------------------------------------------


def test_update_plan_name(api_client, merchant_and_token, make_plan, db):
    merchant, token = merchant_and_token
    plan = make_plan(merchant, name="Old Name")

    resp = api_client.patch(
        f"/v1/plans/{plan.id}",
        json={"name": "New Name"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["plan"]["name"] == "New Name"

    db.refresh(plan)
    assert plan.name == "New Name"


def test_update_plan_trial_days(api_client, merchant_and_token, make_plan, db):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)

    resp = api_client.patch(
        f"/v1/plans/{plan.id}",
        json={"trial_days": 14},
        headers=mut_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["plan"]["trial_days"] == 14

    db.refresh(plan)
    assert plan.trial_days == 14


def test_update_plan_status_to_archived(api_client, merchant_and_token, make_plan, db):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)

    resp = api_client.patch(
        f"/v1/plans/{plan.id}",
        json={"status": "archived"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["plan"]["status"] == "archived"

    db.refresh(plan)
    assert plan.status == PlanStatus.archived


def test_update_plan_other_merchant_returns_404(
    api_client, merchant_and_token, other_merchant_and_token, make_plan
):
    other_merchant, _ = other_merchant_and_token
    plan = make_plan(other_merchant)

    _, token = merchant_and_token
    resp = api_client.patch(
        f"/v1/plans/{plan.id}",
        json={"name": "Hijacked"},
        headers=mut_headers(token),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /v1/plans/{plan_id}  (archive)
# ---------------------------------------------------------------------------


def test_archive_plan_sets_status_archived(api_client, merchant_and_token, make_plan, db):
    merchant, token = merchant_and_token
    plan = make_plan(merchant)

    resp = api_client.delete(f"/v1/plans/{plan.id}", headers=mut_headers(token))
    assert resp.status_code == 200
    assert resp.json()["plan"]["status"] == "archived"

    db.refresh(plan)
    assert plan.status == PlanStatus.archived


def test_archive_already_archived_plan_returns_400(api_client, merchant_and_token, make_plan):
    merchant, token = merchant_and_token
    plan = make_plan(merchant, status=PlanStatus.archived)

    resp = api_client.delete(f"/v1/plans/{plan.id}", headers=mut_headers(token))
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "already_archived"


def test_archive_plan_not_found_returns_404(api_client, merchant_and_token):
    _, token = merchant_and_token
    resp = api_client.delete("/v1/plans/99999", headers=mut_headers(token))
    assert resp.status_code == 404
