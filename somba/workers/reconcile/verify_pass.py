"""Verify pass: resolve payment_uncertain subscriptions by querying Nomba.

For each subscription stuck in payment_uncertain the verify pass:
  1. Finds the pending LedgerIntent (the one with an uncertain ChargeAttempt).
  2. Calls Nomba's transaction-verify endpoint using the order_reference.
  3. Writes a settlement via the ledger writer, which runs the matcher and heals.
  4. If Nomba confirms failure, moves the intent to unmatched and triggers recovery.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.db.models import (
    ChargeAttempt,
    ChargeAttemptStatus,
    LedgerIntent,
    LedgerIntentStatus,
    LedgerSettlementSource,
    LedgerSettlementStatus,
    SubscriptionEventTrigger,
    SubscriptionStatus,
)
from somba.nomba import client as nomba_client
from somba.nomba.client import NombaChargeStatus
from somba.subscriptions.state_machine import transition
from somba.workers.reconcile.writer import write_settlement
from somba.workers.recovery.classifier import classify
from somba.workers.recovery.engine import run as recovery_run

log = logging.getLogger(__name__)

_VERIFY_LIMIT = 100


def run(
    db: Session,
    *,
    nomba_base_url: str | None = None,
    now: datetime | None = None,
    limit: int = _VERIFY_LIMIT,
) -> int:
    """Resolve up to *limit* payment_uncertain subscriptions. Returns count resolved."""
    now = now or datetime.now(tz=timezone.utc)

    # Uncertain ChargeAttempts are our queue for the verify pass
    uncertain_attempts: list[ChargeAttempt] = list(
        db.scalars(
            select(ChargeAttempt)
            .where(ChargeAttempt.status == ChargeAttemptStatus.uncertain)
            .order_by(ChargeAttempt.id)
            .limit(limit)
        )
    )
    log.info("verify_pass: %d uncertain attempts to resolve", len(uncertain_attempts))

    resolved = 0
    for attempt in uncertain_attempts:
        if _resolve_attempt(db, attempt=attempt, nomba_base_url=nomba_base_url, now=now):
            resolved += 1

    return resolved


def _resolve_attempt(
    db: Session,
    *,
    attempt: ChargeAttempt,
    nomba_base_url: str | None,
    now: datetime,
) -> bool:
    result = nomba_client.verify_transaction(
        order_reference=attempt.order_reference,
        base_url=nomba_base_url,
    )
    log.info(
        "verify_pass: order=%s nomba_status=%s",
        attempt.order_reference,
        result.status.value,
    )

    # ChargeAttempt.order_reference is attempt-specific (each attempt gets its
    # own, so retries don't collide on the DB's unique constraint) and won't
    # string-match LedgerIntent.order_reference. Look the intent up via the
    # FK verify_pass's own queue depends on (_handle_uncertain always sets
    # it) instead of by reference.
    intent: LedgerIntent | None = db.scalar(
        select(LedgerIntent).where(LedgerIntent.charge_attempt_id == attempt.id)
    )

    if result.status == NombaChargeStatus.uncertain:
        # Nomba still doesn't know — leave it and try again on the next pass
        log.info("verify_pass: still uncertain order=%s — deferred", attempt.order_reference)
        return False

    if result.status == NombaChargeStatus.succeeded:
        res = write_settlement(
            db,
            merchant_id=attempt.merchant_id,
            order_reference=intent.order_reference if intent else attempt.order_reference,
            transaction_ref=result.transaction_id or f"verify-{attempt.order_reference}",
            amount_kobo=attempt.amount,
            source=LedgerSettlementSource.verify_pass,
            raw_payload=result.raw,
            now=now,
        )
        attempt.status = ChargeAttemptStatus.succeeded
        db.commit()
        log.info(
            "verify_pass: healed sub=%d status=%s",
            attempt.subscription_id,
            res.status.value,
        )
        return True

    # Nomba confirmed failure
    attempt.status = ChargeAttemptStatus.failed
    attempt.failure_reason = result.failure_reason
    failure_class = classify(result.response_code, result.failure_reason)
    attempt.failure_class = failure_class

    if intent:
        intent.status = LedgerIntentStatus.unmatched

    # Revert subscription from payment_uncertain → past_due so recovery can proceed
    from somba.db.models import Subscription
    sub: Subscription | None = db.get(Subscription, attempt.subscription_id)
    if sub and sub.status == SubscriptionStatus.payment_uncertain:
        transition(
            sub,
            SubscriptionStatus.past_due,
            SubscriptionEventTrigger.reconciliation,
            db,
            metadata={"charge_attempt_id": attempt.id, "failure_class": failure_class.value},
        )

    if sub and intent:
        recovery_run(
            db,
            merchant_id=attempt.merchant_id,
            subscription_id=attempt.subscription_id,
            invoice_id=attempt.invoice_id,
            charge_attempt_id=attempt.id,
            failure_class=failure_class,
            attempt_number=attempt.attempt_number,
            now=now,
        )

    db.commit()
    log.info(
        "verify_pass: confirmed failure sub=%d class=%s",
        attempt.subscription_id,
        failure_class.value,
    )
    return True
