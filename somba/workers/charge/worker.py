"""Charge worker: read due billing rows, acquire locks, write ledger intents."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.db.models import (
    Invoice,
    InvoiceStatus,
    InvoiceType,
    LedgerIntent,
    LedgerIntentStatus,
    Plan,
)
from somba.scheduler.billing_sweep import acquire_billing_lock, fetch_due_subscriptions

log = logging.getLogger(__name__)


def run(db: Session, cutoff: datetime | None = None) -> int:
    """Process one sweep batch. Returns number of intents written."""
    cutoff = cutoff or datetime.now(tz=timezone.utc)
    due = fetch_due_subscriptions(db, cutoff)
    log.info("charge_worker: %d subscriptions due at %s", len(due), cutoff.isoformat())

    written = 0
    for sub in due:
        billing_period = cutoff.date()

        if not acquire_billing_lock(db, sub.id, billing_period):
            continue

        invoice = _get_or_create_open_invoice(db, sub, cutoff)

        intent_idem_key = f"charge-{sub.id}-{billing_period.isoformat()}"
        existing = db.scalar(
            select(LedgerIntent).where(LedgerIntent.idempotency_key == intent_idem_key)
        )
        if existing:
            log.debug("charge_worker: intent already exists sub=%d", sub.id)
            continue

        db.add(
            LedgerIntent(
                merchant_id=sub.merchant_id,
                subscription_id=sub.id,
                invoice_id=invoice.id,
                idempotency_key=intent_idem_key,
                order_reference=f"order-{uuid.uuid4().hex}",
                amount=invoice.amount,
                status=LedgerIntentStatus.pending,
            )
        )
        db.commit()
        log.info("charge_worker: intent written sub=%d invoice=%d", sub.id, invoice.id)
        written += 1

    return written


def _get_or_create_open_invoice(db: Session, sub: object, cutoff: datetime) -> Invoice:
    """Return the existing open invoice for this period or create a draft one."""
    existing = db.scalar(
        select(Invoice).where(
            Invoice.subscription_id == sub.id,
            Invoice.status == InvoiceStatus.open,
            Invoice.period_start == sub.current_period_start,
        )
    )
    if existing:
        return existing

    plan: Plan = db.get(Plan, sub.plan_id)
    invoice = Invoice(
        merchant_id=sub.merchant_id,
        subscription_id=sub.id,
        customer_id=sub.customer_id,
        amount=plan.amount,
        status=InvoiceStatus.open,
        type=InvoiceType.regular,
        period_start=sub.current_period_start,
        period_end=sub.current_period_end,
        due_date=cutoff,
    )
    db.add(invoice)
    db.flush()
    return invoice
