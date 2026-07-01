"""Integration test: full billing cycle — create -> bill -> heal.

Unlike the smoke test (immediate success), this exercises the recovery path:
the first charge attempt fails (subscription -> past_due, invoice stays
open), and a later settlement (e.g. a delayed Nomba confirmation, or the
reconciliation sweep matching an account transaction) heals it back to
active with the invoice marked paid.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from sqlalchemy import select

from somba.db.models import (
    ChargeAttempt,
    ChargeAttemptStatus,
    Customer,
    Invoice,
    InvoiceStatus,
    LedgerIntent,
    LedgerIntentStatus,
    LedgerSettlementSource,
    OutboxEvent,
    SubscriptionStatus,
)
from somba.nomba.client import NombaChargeResult, NombaChargeStatus
from somba.workers.charge.worker import execute_pending
from somba.workers.charge.worker import run as billing_run
from somba.workers.reconcile.writer import write_settlement


def _mock_debit_failure(**kwargs) -> NombaChargeResult:
    return NombaChargeResult(
        status=NombaChargeStatus.failed,
        transaction_id=None,
        failure_reason="insufficient_funds",
        response_code="51",
        raw={},
    )


def test_full_billing_cycle_create_bill_heal(api_client, merchant_and_token, db):
    merchant, token = merchant_and_token
    auth = {"Authorization": f"Bearer {token}"}

    # 1. Create plan + customer + subscription via the API (the "create" phase).
    plan_resp = api_client.post(
        "/v1/plans",
        json={"name": "Monthly Basic", "amount": 7500, "interval": "month", "currency": "NGN"},
        headers={**auth, "Idempotency-Key": "heal-plan-1"},
    )
    assert plan_resp.status_code == 201, plan_resp.json()
    plan_id = plan_resp.json()["plan"]["id"]

    cust_resp = api_client.post(
        "/v1/customers",
        json={"email": "heal@test.com", "name": "Heal User"},
        headers={**auth, "Idempotency-Key": "heal-cust-1"},
    )
    assert cust_resp.status_code == 201, cust_resp.json()
    cust_id = cust_resp.json()["customer"]["id"]

    customer = db.get(Customer, cust_id)
    customer.mandate_id = "mandate-heal-1"
    db.commit()

    sub_resp = api_client.post(
        "/v1/subscriptions",
        json={"customer_id": cust_id, "plan_id": plan_id},
        headers={**auth, "Idempotency-Key": "heal-sub-1"},
    )
    assert sub_resp.status_code == 201, sub_resp.json()
    sub_id = sub_resp.json()["subscription"]["id"]

    # 2. Bill: sweep writes the intent, execute calls Nomba (mocked to fail).
    cutoff = datetime.now(tz=timezone.utc) + timedelta(seconds=5)
    written = billing_run(db, cutoff=cutoff)
    assert written == 1

    with patch("somba.nomba.client.debit_mandate", side_effect=_mock_debit_failure):
        processed = execute_pending(db, now=cutoff)
    assert processed == 1

    # Subscription is now past_due; invoice is still open; intent unmatched.
    sub_resp = api_client.get(f"/v1/subscriptions/{sub_id}", headers=auth)
    assert sub_resp.json()["subscription"]["status"] == "past_due"

    invoice = db.scalar(select(Invoice).where(Invoice.subscription_id == sub_id))
    assert invoice.status == InvoiceStatus.open

    attempt = db.scalar(select(ChargeAttempt).where(ChargeAttempt.subscription_id == sub_id))
    assert attempt.status == ChargeAttemptStatus.failed

    intent = db.scalar(select(LedgerIntent).where(LedgerIntent.subscription_id == sub_id))
    assert intent.status == LedgerIntentStatus.unmatched

    # 3. Heal: a settlement for the same order_reference arrives later (e.g. a
    # delayed webhook, or the sweep matching the transaction on Nomba's side).
    result = write_settlement(
        db,
        merchant_id=merchant.id,
        order_reference=intent.order_reference,
        transaction_ref="tx-heal-late-001",
        amount_kobo=intent.amount,
        source=LedgerSettlementSource.webhook,
        raw_payload={},
        now=cutoff + timedelta(minutes=10),
    )
    db.commit()
    assert result.healed is True

    # 4. Subscription active again, invoice paid, charge attempt marked succeeded.
    sub_resp = api_client.get(f"/v1/subscriptions/{sub_id}", headers=auth)
    assert sub_resp.json()["subscription"]["status"] == "active"

    db.refresh(invoice)
    assert invoice.status == InvoiceStatus.paid

    db.refresh(attempt)
    assert attempt.status == ChargeAttemptStatus.succeeded

    healed_event = db.scalar(
        select(OutboxEvent).where(
            OutboxEvent.event_type == "charge.succeeded",
            OutboxEvent.aggregate_id == str(sub_id),
        )
    )
    assert healed_event is not None

    # 5. /v1/metrics reflects the recovery: one past_due, one healed.
    metrics = api_client.get("/v1/metrics", headers=auth).json()["metrics"]
    assert metrics["past_due_total"] == 1
    assert metrics["past_due_healed"] == 1
    assert metrics["recovery_rate"] == 1.0
    assert metrics["pending_intents"] == 0
