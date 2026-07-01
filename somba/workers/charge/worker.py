"""Charge worker: billing sweep → intents, then intent → Nomba → settlement."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.db.models import (
    ChargeAttempt,
    ChargeAttemptStatus,
    Customer,
    FailureClass,
    Invoice,
    InvoiceStatus,
    InvoiceType,
    LedgerIntent,
    LedgerIntentStatus,
    LedgerSettlement,
    LedgerSettlementSource,
    LedgerSettlementStatus,
    OutboxEvent,
    OutboxEventStatus,
    Plan,
    Subscription,
    SubscriptionEventTrigger,
    SubscriptionStatus,
)
from somba.nomba import client as nomba_client
from somba.nomba.client import NombaChargeStatus
from somba.scheduler.billing_sweep import acquire_billing_lock, fetch_due_subscriptions
from somba.subscriptions.period import next_period_end
from somba.subscriptions.state_machine import transition
from somba.workers.recovery.classifier import classify
from somba.workers.recovery.engine import run as recovery_run

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Phase 1: billing sweep → write ledger intents
# ---------------------------------------------------------------------------


def run(db: Session, cutoff: datetime | None = None) -> int:
    """Find due subscriptions and write one LedgerIntent per billing period.

    Returns the number of intents written.
    """
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


# ---------------------------------------------------------------------------
# Phase 2: execute pending intents → Nomba call → parse → publish
# ---------------------------------------------------------------------------

_EXECUTE_LIMIT = 200


def execute_pending(
    db: Session,
    *,
    nomba_base_url: str | None = None,
    now: datetime | None = None,
    limit: int = _EXECUTE_LIMIT,
) -> int:
    """Read pending LedgerIntents, call Nomba, record ChargeAttempt, handle result.

    Returns the number of intents processed (regardless of outcome).
    """
    now = now or datetime.now(tz=timezone.utc)
    intents: list[LedgerIntent] = list(
        db.scalars(
            select(LedgerIntent)
            .where(LedgerIntent.status == LedgerIntentStatus.pending)
            .order_by(LedgerIntent.id)
            .limit(limit)
        )
    )
    log.info("charge_worker.execute: %d pending intents", len(intents))

    processed = 0
    for intent in intents:
        _execute_one(db, intent, nomba_base_url=nomba_base_url, now=now)
        processed += 1

    return processed


def _execute_one(
    db: Session,
    intent: LedgerIntent,
    *,
    nomba_base_url: str | None,
    now: datetime,
) -> None:
    sub: Subscription = db.get(Subscription, intent.subscription_id)
    customer: Customer = db.get(Customer, sub.customer_id)
    invoice: Invoice = db.get(Invoice, intent.invoice_id)

    # Derive billing period from invoice for a stable, date-safe key
    billing_period = (
        invoice.period_start.date()
        if invoice.period_start
        else now.date()
    )

    # Count prior attempts to build the attempt_number
    prior_attempts: int = db.query(ChargeAttempt).filter(
        ChargeAttempt.subscription_id == sub.id,
        ChargeAttempt.invoice_id == invoice.id,
    ).count()
    attempt_number = prior_attempts + 1

    # Idempotency key: charge_{sub}_{period}_{attempt}
    idem_key = f"charge_{sub.id}_{billing_period.isoformat()}_{attempt_number}"
    existing_attempt = db.scalar(
        select(ChargeAttempt).where(ChargeAttempt.idempotency_key == idem_key)
    )
    if existing_attempt:
        log.debug("charge_worker.execute: attempt already exists sub=%d key=%s", sub.id, idem_key)
        return

    _log_billing_lag(sub, now)

    # ChargeAttempt.order_reference is unique per-row, but intent.order_reference
    # is fixed for the intent's whole lifetime -- reusing it verbatim would
    # collide on any second attempt (a retry, or reprocessing after
    # "uncertain") with a UniqueViolation, silently aborting the whole
    # execute_pending() batch. Suffix by attempt_number so every attempt gets
    # its own row while still being traceable back to the parent intent.
    attempt_order_ref = f"{intent.order_reference}-{attempt_number}"

    if not customer.mandate_id:
        log.warning("charge_worker.execute: no mandate_id for customer=%d sub=%d", customer.id, sub.id)
        _handle_failure(db, intent=intent, sub=sub, invoice=invoice, attempt_number=attempt_number,
                        idem_key=idem_key, order_reference=attempt_order_ref,
                        reason="no_mandate_id", code=None, now=now)
        return

    # Call Nomba direct debit
    result = nomba_client.debit_mandate(
        mandate_id=customer.mandate_id,
        amount_kobo=intent.amount,
        base_url=nomba_base_url,
    )
    log.info(
        "charge_worker.execute: nomba=%s sub=%d attempt=%d order=%s",
        result.status.value,
        sub.id,
        attempt_number,
        attempt_order_ref,
    )

    if result.status == NombaChargeStatus.succeeded:
        _handle_success(db, intent=intent, sub=sub, invoice=invoice,
                        attempt_number=attempt_number, idem_key=idem_key, order_reference=attempt_order_ref,
                        transaction_id=result.transaction_id, now=now)

    elif result.status == NombaChargeStatus.failed:
        _handle_failure(db, intent=intent, sub=sub, invoice=invoice,
                        attempt_number=attempt_number, idem_key=idem_key, order_reference=attempt_order_ref,
                        reason=result.failure_reason, code=result.response_code, now=now)

    else:  # uncertain
        _handle_uncertain(db, intent=intent, sub=sub,
                          attempt_number=attempt_number, idem_key=idem_key, order_reference=attempt_order_ref,
                          reason=result.failure_reason, now=now)


def _handle_success(
    db: Session,
    *,
    intent: LedgerIntent,
    sub: Subscription,
    invoice: Invoice,
    attempt_number: int,
    idem_key: str,
    order_reference: str,
    transaction_id: str | None,
    now: datetime,
) -> None:
    attempt = ChargeAttempt(
        merchant_id=sub.merchant_id,
        subscription_id=sub.id,
        invoice_id=invoice.id,
        idempotency_key=idem_key,
        order_reference=order_reference,
        amount=intent.amount,
        status=ChargeAttemptStatus.succeeded,
        attempt_number=attempt_number,
    )
    db.add(attempt)
    db.flush()

    intent.status = LedgerIntentStatus.matched
    intent.charge_attempt_id = attempt.id

    db.add(LedgerSettlement(
        merchant_id=sub.merchant_id,
        intent_id=intent.id,
        invoice_id=invoice.id,
        order_reference=intent.order_reference,
        transaction_ref=transaction_id or "",
        amount=intent.amount,
        source=LedgerSettlementSource.direct_debit,
        status=LedgerSettlementStatus.matched,
        raw_payload={"transaction_id": transaction_id},
    ))

    invoice.status = InvoiceStatus.paid
    invoice.paid_at = now

    if sub.status in (SubscriptionStatus.past_due, SubscriptionStatus.trialing):
        transition(sub, SubscriptionStatus.active, SubscriptionEventTrigger.scheduler, db,
                   metadata={"charge_attempt_id": attempt.id})

    # Advance to the next billing period -- but only for a regular billing
    # invoice. A proration invoice bills a mid-cycle top-up on the CURRENT
    # period and must not move it. Without this, next_bill_date never
    # changes: the subscription is picked up as "due" again the very next
    # day, and the second attempt crashes outright on
    # uq_invoices_subscription_period_start (same period_start, same sub).
    if invoice.type == InvoiceType.regular:
        plan: Plan = db.get(Plan, sub.plan_id)
        new_period_start = sub.current_period_end or now
        sub.current_period_start = new_period_start
        sub.current_period_end = next_period_end(plan.interval, plan.interval_count, new_period_start)
        sub.next_bill_date = sub.current_period_end

    db.add(_outbox(
        merchant_id=sub.merchant_id,
        aggregate_id=str(sub.id),
        event_type="charge.succeeded",
        payload={
            "subscription_id": sub.id,
            "invoice_id": invoice.id,
            "amount": intent.amount,
            "charge_attempt_id": attempt.id,
        },
    ))
    db.commit()
    log.info("charge_worker.execute: succeeded sub=%d invoice=%d", sub.id, invoice.id)


def _handle_failure(
    db: Session,
    *,
    intent: LedgerIntent,
    sub: Subscription,
    invoice: Invoice,
    attempt_number: int,
    idem_key: str,
    order_reference: str,
    reason: str | None,
    code: str | None,
    now: datetime,
) -> None:
    failure_class: FailureClass = classify(code, reason)

    attempt = ChargeAttempt(
        merchant_id=sub.merchant_id,
        subscription_id=sub.id,
        invoice_id=invoice.id,
        idempotency_key=idem_key,
        order_reference=order_reference,
        amount=intent.amount,
        status=ChargeAttemptStatus.failed,
        failure_reason=reason,
        failure_class=failure_class,
        attempt_number=attempt_number,
    )
    db.add(attempt)
    db.flush()

    intent.status = LedgerIntentStatus.unmatched
    intent.charge_attempt_id = attempt.id

    # Transition subscription to past_due if it isn't already
    if sub.status == SubscriptionStatus.active:
        transition(sub, SubscriptionStatus.past_due, SubscriptionEventTrigger.scheduler, db,
                   metadata={"charge_attempt_id": attempt.id, "failure_class": failure_class.value})
    elif sub.status == SubscriptionStatus.trialing:
        transition(sub, SubscriptionStatus.past_due, SubscriptionEventTrigger.scheduler, db,
                   metadata={"charge_attempt_id": attempt.id, "failure_class": failure_class.value})

    action = recovery_run(
        db,
        merchant_id=sub.merchant_id,
        subscription_id=sub.id,
        invoice_id=invoice.id,
        charge_attempt_id=attempt.id,
        failure_class=failure_class,
        attempt_number=attempt_number,
        now=now,
    )

    db.add(_outbox(
        merchant_id=sub.merchant_id,
        aggregate_id=str(sub.id),
        event_type="charge.failed",
        payload={
            "subscription_id": sub.id,
            "invoice_id": invoice.id,
            "charge_attempt_id": attempt.id,
            "failure_class": failure_class.value,
            "failure_reason": reason,
            "recovery_action": action,
        },
    ))
    db.commit()
    log.info("charge_worker.execute: failed sub=%d class=%s action=%s", sub.id, failure_class.value, action)


def _handle_uncertain(
    db: Session,
    *,
    intent: LedgerIntent,
    sub: Subscription,
    attempt_number: int,
    idem_key: str,
    order_reference: str,
    reason: str | None,
    now: datetime,
) -> None:
    attempt = ChargeAttempt(
        merchant_id=sub.merchant_id,
        subscription_id=sub.id,
        invoice_id=intent.invoice_id,
        idempotency_key=idem_key,
        order_reference=order_reference,
        amount=intent.amount,
        status=ChargeAttemptStatus.uncertain,
        failure_reason=reason,
        attempt_number=attempt_number,
    )
    db.add(attempt)
    db.flush()

    intent.charge_attempt_id = attempt.id
    # Keep intent as pending so the verify pass can resolve it later

    if sub.status == SubscriptionStatus.trialing:
        # payment_uncertain is only reachable from active/past_due — a charge
        # attempt means the trial is effectively over, so land on active first.
        transition(sub, SubscriptionStatus.active, SubscriptionEventTrigger.scheduler, db,
                   metadata={"charge_attempt_id": attempt.id})

    if sub.status in (SubscriptionStatus.active, SubscriptionStatus.past_due):
        transition(sub, SubscriptionStatus.payment_uncertain, SubscriptionEventTrigger.scheduler, db,
                   metadata={"charge_attempt_id": attempt.id, "reason": reason})

    db.add(_outbox(
        merchant_id=sub.merchant_id,
        aggregate_id=str(sub.id),
        event_type="charge.uncertain",
        payload={
            "subscription_id": sub.id,
            "invoice_id": intent.invoice_id,
            "charge_attempt_id": attempt.id,
        },
    ))
    db.commit()
    log.info("charge_worker.execute: uncertain sub=%d attempt=%d", sub.id, attempt_number)


def _outbox(*, merchant_id: int, aggregate_id: str, event_type: str, payload: dict) -> OutboxEvent:
    return OutboxEvent(
        merchant_id=merchant_id,
        aggregate_type="subscription",
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
        partition_key=aggregate_id,
        status=OutboxEventStatus.pending,
    )


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _log_billing_lag(sub: Subscription, now: datetime) -> None:
    """Log the delay between when a subscription came due and this attempt.

    Surfaces scheduler/worker backlog: a growing lag means due subscriptions
    are sitting around before being charged.
    """
    if sub.next_bill_date is None:
        return
    next_bill = sub.next_bill_date if sub.next_bill_date.tzinfo else sub.next_bill_date.replace(tzinfo=timezone.utc)
    lag_seconds = (now - next_bill).total_seconds()
    log.info("billing_lag_seconds sub=%d lag_seconds=%.1f", sub.id, lag_seconds)


def _get_or_create_open_invoice(db: Session, sub: Subscription, cutoff: datetime) -> Invoice:
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
