"""Golden path smoke test: full subscription billing lifecycle end-to-end.

Exercises the complete happy path:
  1. Create plan + customer + subscription via HTTP API
  2. Run billing sweep (charge worker phase 1) — writes LedgerIntent
  3. Run execute_pending (charge worker phase 2) with mocked Nomba success
  4. Assert invoice is paid
  5. Assert charge.succeeded event is in outbox
  6. Assert /v1/metrics reflects the active subscription
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from sqlalchemy import select

from somba.db.models import (
    Customer,
    Invoice,
    InvoiceStatus,
    OutboxEvent,
    OutboxEventStatus,
)
from somba.nomba.client import NombaChargeResult, NombaChargeStatus
from somba.workers.charge.worker import execute_pending
from somba.workers.charge.worker import run as billing_run


def _mock_debit_success(**kwargs) -> NombaChargeResult:
    return NombaChargeResult(
        status=NombaChargeStatus.succeeded,
        transaction_id="txn-smoke-001",
        failure_reason=None,
        response_code="00",
        raw={},
    )


def test_full_billing_lifecycle(api_client, merchant_and_token, db):
    """Create plan → customer → subscription, sweep, charge, verify paid invoice."""
    merchant, token = merchant_and_token
    auth = {"Authorization": f"Bearer {token}"}

    # 1. Create plan (no trial — next_bill_date = now on subscription creation)
    plan_resp = api_client.post(
        "/v1/plans",
        json={"name": "Monthly Basic", "amount": 5000, "interval": "month", "currency": "NGN"},
        headers={**auth, "Idempotency-Key": "smoke-plan-1"},
    )
    assert plan_resp.status_code == 201, plan_resp.json()
    plan_id = plan_resp.json()["plan"]["id"]

    # 2. Create customer
    cust_resp = api_client.post(
        "/v1/customers",
        json={"email": "smoke@test.com", "name": "Smoke User"},
        headers={**auth, "Idempotency-Key": "smoke-cust-1"},
    )
    assert cust_resp.status_code == 201, cust_resp.json()
    cust_id = cust_resp.json()["customer"]["id"]

    # Attach mandate directly — the customer API doesn't expose this field yet
    customer = db.get(Customer, cust_id)
    customer.mandate_id = "mandate-smoke-1"
    db.commit()

    # 3. Create subscription — no trial, so status=active, next_bill_date=now
    sub_resp = api_client.post(
        "/v1/subscriptions",
        json={"customer_id": cust_id, "plan_id": plan_id},
        headers={**auth, "Idempotency-Key": "smoke-sub-1"},
    )
    assert sub_resp.status_code == 201, sub_resp.json()
    sub_data = sub_resp.json()["subscription"]
    sub_id = sub_data["id"]
    assert sub_data["status"] == "active"

    # 4. Billing sweep: find due subscriptions → write LedgerIntent
    cutoff = datetime.now(tz=timezone.utc) + timedelta(seconds=5)
    intents_written = billing_run(db, cutoff=cutoff)
    assert intents_written == 1, f"Expected 1 intent written, got {intents_written}"

    # 5. Execute pending intents — mock Nomba to confirm success
    with patch("somba.nomba.client.debit_mandate", side_effect=_mock_debit_success):
        processed = execute_pending(db, now=cutoff)
    assert processed == 1

    # 6. Invoice is now paid
    invoice = db.scalar(
        select(Invoice).where(
            Invoice.subscription_id == sub_id,
            Invoice.status == InvoiceStatus.paid,
        )
    )
    assert invoice is not None, "Invoice should be paid after a successful charge"
    assert invoice.amount == 5000

    # 7. Outbox contains charge.succeeded (pending relay to Kafka)
    charge_event = db.scalar(
        select(OutboxEvent).where(
            OutboxEvent.event_type == "charge.succeeded",
            OutboxEvent.aggregate_id == str(sub_id),
        )
    )
    assert charge_event is not None, "Expected charge.succeeded in outbox"
    assert charge_event.status == OutboxEventStatus.pending

    # 8. /v1/metrics reflects the state
    metrics_resp = api_client.get("/v1/metrics", headers=auth)
    assert metrics_resp.status_code == 200
    m = metrics_resp.json()["metrics"]
    assert m["active_subscriptions"] >= 1
    # subscription.created + charge.succeeded are both pending relay
    assert m["outbox_pending_events"] >= 2
    assert m["pending_intents"] == 0      # intent was resolved by the charge
    assert m["payment_uncertain_subscriptions"] == 0
