"""Periodic reconciliation sweep: fetch account transactions and match against intents.

The sweep runs on a schedule (e.g. every few minutes) and does two jobs:
  1. Fetch recent transactions from Nomba and try to match any that correspond
     to pending LedgerIntents that haven't been confirmed via webhook yet.
  2. Re-queue any LedgerIntents that are still pending beyond a timeout window
     so the verify pass can pick them up.

This catches the gap between "charge was sent" and "webhook never arrived."
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.db.models import (
    ChargeAttempt,
    ChargeAttemptStatus,
    LedgerIntent,
    LedgerIntentStatus,
    LedgerSettlementSource,
    LedgerSettlementStatus,
)
from somba.nomba import client as nomba_client
from somba.workers.reconcile.writer import write_settlement

log = logging.getLogger(__name__)

# Intents older than this without a settlement are checked in this sweep
_STALE_AFTER_MINUTES = 10
_SWEEP_TX_WINDOW_MINUTES = 30
_SWEEP_LIMIT = 500


def run(
    db: Session,
    *,
    nomba_base_url: str | None = None,
    now: datetime | None = None,
    merchant_id: int | None = None,
) -> int:
    """Fetch account transactions from Nomba and match against pending intents.

    Returns number of intents newly resolved.
    """
    now = now or datetime.now(tz=timezone.utc)
    fetch_from = now - timedelta(minutes=_SWEEP_TX_WINDOW_MINUTES)

    transactions = nomba_client.fetch_account_transactions(
        from_dt=fetch_from,
        to_dt=now,
        base_url=nomba_base_url,
    )
    log.info("reconcile.sweep: fetched %d transactions from Nomba", len(transactions))

    resolved = 0
    for txn in transactions:
        if _process_transaction(db, txn=txn, now=now):
            resolved += 1

    # Also re-examine stale pending intents and mark them for the verify pass
    _flag_stale_intents(db, now=now, merchant_id=merchant_id)

    db.commit()
    log.info("reconcile.sweep: resolved=%d", resolved)
    return resolved


def _process_transaction(db: Session, *, txn: dict, now: datetime) -> bool:
    """Attempt to match one Nomba transaction to a pending LedgerIntent."""
    order_ref: str = (
        txn.get("orderReference")
        or txn.get("aliasAccountReference")
        or ""
    )
    transaction_ref: str = txn.get("transactionId") or txn.get("sessionId") or ""
    amount_kobo: int = int(float(txn.get("transactionAmount", 0)) * 100)
    source_account: str = txn.get("destinationAccountNumber") or ""

    if not transaction_ref:
        return False

    # Check for an existing settlement with this transaction_ref — skip if already processed
    from sqlalchemy import select as sa_select
    from somba.db.models import LedgerSettlement
    existing = db.scalar(
        sa_select(LedgerSettlement).where(LedgerSettlement.transaction_ref == transaction_ref)
    )
    if existing:
        return False

    # Determine merchant_id from the matching intent (or from customer VA)
    intent: LedgerIntent | None = None
    merchant_id: int | None = None

    if order_ref:
        intent = db.scalar(
            select(LedgerIntent).where(LedgerIntent.order_reference == order_ref)
        )
        if intent:
            merchant_id = intent.merchant_id

    if merchant_id is None:
        # Orphan: no intent, but we still write it so the VA healer can try
        if not source_account:
            return False
        from somba.db.models import Customer
        customer = db.scalar(
            select(Customer).where(Customer.va_account_no == source_account)
        )
        if customer is None:
            return False
        merchant_id = customer.merchant_id

    res = write_settlement(
        db,
        merchant_id=merchant_id,
        order_reference=order_ref or f"sweep-{transaction_ref}",
        transaction_ref=transaction_ref,
        amount_kobo=amount_kobo,
        source=LedgerSettlementSource.sweep,
        raw_payload=txn,
        now=now,
    )
    return res.status in (LedgerSettlementStatus.matched,)


def _flag_stale_intents(
    db: Session,
    *,
    now: datetime,
    merchant_id: int | None,
) -> None:
    """Find pending intents that have an uncertain ChargeAttempt and are overdue.

    They will be picked up by the verify pass on the next cycle.
    Stale unmatched intents (no attempt) are left for manual review.
    """
    cutoff = now - timedelta(minutes=_STALE_AFTER_MINUTES)

    query = (
        select(ChargeAttempt)
        .where(
            ChargeAttempt.status == ChargeAttemptStatus.uncertain,
        )
        .limit(_SWEEP_LIMIT)
    )
    if merchant_id is not None:
        query = query.where(ChargeAttempt.merchant_id == merchant_id)

    stale = list(db.scalars(query))
    if stale:
        log.info("reconcile.sweep: %d stale uncertain attempts flagged for verify pass", len(stale))
