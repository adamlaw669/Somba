"""Nomba inbound webhook handler."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from somba.db.models import (
    ChargeAttempt,
    ChargeAttemptStatus,
    LedgerIntent,
    LedgerIntentStatus,
    LedgerSettlement,
    LedgerSettlementSource,
    LedgerSettlementStatus,
)
from somba.db.session import get_db
from somba.nomba.intake import verify_nomba_signature

router = APIRouter()
log = logging.getLogger(__name__)


def _handle_payment_success(db: Session, payload: dict[str, Any]) -> None:
    transaction = payload.get("data", {}).get("transaction", {})
    order_ref = transaction.get("aliasAccountReference", "")
    transaction_ref = transaction.get("transactionId") or transaction.get("sessionId", "")
    amount_kobo = int(transaction.get("transactionAmount", 0) * 100)

    intent = (
        db.query(LedgerIntent)
        .filter(
            LedgerIntent.order_reference == order_ref,
            LedgerIntent.status == LedgerIntentStatus.pending,
        )
        .first()
    )

    if intent is None:
        log.warning("nomba webhook: no pending intent for order_reference=%s tx=%s", order_ref, transaction_ref)
        return

    db.add(LedgerSettlement(
        merchant_id=intent.merchant_id,
        intent_id=intent.id,
        invoice_id=intent.invoice_id,
        order_reference=order_ref,
        transaction_ref=transaction_ref,
        amount=amount_kobo,
        source=LedgerSettlementSource.webhook,
        status=LedgerSettlementStatus.matched,
        raw_payload=payload,
    ))

    intent.status = LedgerIntentStatus.matched

    attempt = (
        db.query(ChargeAttempt)
        .filter(ChargeAttempt.order_reference == order_ref)
        .first()
    )
    if attempt:
        attempt.status = ChargeAttemptStatus.succeeded

    db.commit()
    log.info("nomba webhook: matched intent=%d tx=%s amount=%d kobo", intent.id, transaction_ref, amount_kobo)


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
