"""Nomba inbound webhook handler."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.db.models import (
    Customer,
    LedgerIntent,
    LedgerSettlementSource,
)
from somba.db.session import get_db
from somba.nomba.intake import verify_nomba_signature
from somba.workers.reconcile.writer import write_settlement

router = APIRouter()
log = logging.getLogger(__name__)


def _handle_payment_success(db: Session, payload: dict[str, Any]) -> None:
    transaction = payload.get("data", {}).get("transaction", {})
    order_ref: str = transaction.get("aliasAccountReference", "")
    transaction_ref: str = transaction.get("transactionId") or transaction.get("sessionId", "")
    amount_kobo: int = int(float(transaction.get("transactionAmount", 0)) * 100)

    if not transaction_ref:
        log.warning("nomba webhook: missing transaction_ref — skipping")
        return

    # Resolve merchant_id: from matching intent, or from VA customer
    intent: LedgerIntent | None = db.scalar(
        select(LedgerIntent).where(LedgerIntent.order_reference == order_ref)
    ) if order_ref else None

    merchant_id: int | None = intent.merchant_id if intent else _merchant_id_from_va(db, payload)
    if merchant_id is None:
        log.warning("nomba webhook: cannot determine merchant for tx=%s order=%s", transaction_ref, order_ref)
        return

    res = write_settlement(
        db,
        merchant_id=merchant_id,
        order_reference=order_ref,
        transaction_ref=transaction_ref,
        amount_kobo=amount_kobo,
        source=LedgerSettlementSource.webhook,
        raw_payload=payload,
    )
    db.commit()
    log.info(
        "nomba webhook: settlement=%d status=%s healed=%s tx=%s",
        res.settlement.id,
        res.status.value,
        res.healed,
        transaction_ref,
    )


def _merchant_id_from_va(db: Session, payload: dict[str, Any]) -> int | None:
    txn = payload.get("data", {}).get("transaction", {})
    va_no: str = (
        txn.get("destinationAccountNumber")
        or txn.get("beneficiaryAccountNumber")
        or ""
    )
    if not va_no:
        return None
    customer: Customer | None = db.scalar(
        select(Customer).where(Customer.va_account_no == va_no)
    )
    return customer.merchant_id if customer else None


@router.post("/v1/webhooks/nomba")
async def nomba_webhook(
    request: Request,
    db: Session = Depends(get_db),
    nomba_timestamp: str = Header(..., alias="nomba-timestamp"),
    nomba_signature: str = Header(..., alias="nomba-signature"),
) -> dict[str, bool]:
    body = await request.json()

    if not verify_nomba_signature(body, nomba_timestamp, nomba_signature):
        log.warning("nomba webhook: invalid signature rejected")
        return JSONResponse(status_code=401, content={"error": "invalid_signature"})

    event_type = body.get("event_type", "")
    log.info("nomba webhook: event_type=%s request_id=%s", event_type, body.get("requestId"))

    if event_type == "payment_success":
        _handle_payment_success(db, body)

    return {"received": True}
