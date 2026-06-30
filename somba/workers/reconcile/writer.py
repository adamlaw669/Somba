"""Centralised ledger writer: intents before every charge, settlements on confirmation.

Intent writer  – called once per billing period before the Nomba charge call.
Settlement writer – called by the webhook handler, verify pass, and sweep whenever
                   a confirmed transaction arrives; runs the matcher inline and
                   performs healing when a match is found.

Matcher decision table (for a new settlement)
----------------------------------------------
order_ref not found in intents            → orphan
order_ref found, intent already matched   → duplicate
order_ref found, intent pending, Δ≠0     → anomaly   (drift)
order_ref found, intent pending, Δ=0     → matched
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.db.models import (
    ChargeAttempt,
    ChargeAttemptStatus,
    Customer,
    Invoice,
    InvoiceStatus,
    LedgerIntent,
    LedgerIntentStatus,
    LedgerSettlement,
    LedgerSettlementSource,
    LedgerSettlementStatus,
    OutboxEvent,
    OutboxEventStatus,
    Subscription,
    SubscriptionEventTrigger,
    SubscriptionStatus,
)
from somba.subscriptions.state_machine import transition

log = logging.getLogger(__name__)

_AMOUNT_TOLERANCE_KOBO = 0  # exact match required; set > 0 to allow rounding drift


# ---------------------------------------------------------------------------
# Intent writer
# ---------------------------------------------------------------------------


def write_intent(
    db: Session,
    *,
    merchant_id: int,
    subscription_id: int,
    invoice_id: int,
    order_reference: str,
    amount: int,
    idempotency_key: str,
) -> LedgerIntent:
    """Create and flush a LedgerIntent.

    Idempotent: if an intent with the same idempotency_key already exists it is
    returned unchanged so callers can safely retry.  The caller owns the commit.
    """
    existing = db.scalar(
        select(LedgerIntent).where(LedgerIntent.idempotency_key == idempotency_key)
    )
    if existing:
        return existing

    intent = LedgerIntent(
        merchant_id=merchant_id,
        subscription_id=subscription_id,
        invoice_id=invoice_id,
        idempotency_key=idempotency_key,
        order_reference=order_reference,
        amount=amount,
        status=LedgerIntentStatus.pending,
    )
    db.add(intent)
    db.flush()
    log.info(
        "ledger.write_intent: intent=%d sub=%d order=%s amount=%d",
        intent.id, subscription_id, order_reference, amount,
    )
    return intent


# ---------------------------------------------------------------------------
# Settlement writer + matcher
# ---------------------------------------------------------------------------


@dataclass
class SettlementResult:
    settlement: LedgerSettlement
    status: LedgerSettlementStatus
    intent: LedgerIntent | None
    healed: bool  # True if subscription was advanced to active


def write_settlement(
    db: Session,
    *,
    merchant_id: int,
    order_reference: str,
    transaction_ref: str,
    amount_kobo: int,
    source: LedgerSettlementSource,
    raw_payload: dict[str, Any],
    now: datetime | None = None,
) -> SettlementResult:
    """Write a LedgerSettlement, run the matcher, heal on match.

    The caller owns the commit.  Returns a SettlementResult describing what
    happened so callers can branch on the outcome.
    """
    now = now or datetime.now(tz=timezone.utc)

    # Guard: don't create duplicate settlements for the same transaction
    existing = db.scalar(
        select(LedgerSettlement).where(LedgerSettlement.transaction_ref == transaction_ref)
    )
    if existing:
        log.info("ledger.write_settlement: duplicate tx=%s — skipped", transaction_ref)
        intent = db.get(LedgerIntent, existing.intent_id) if existing.intent_id else None
        return SettlementResult(
            settlement=existing,
            status=LedgerSettlementStatus.duplicate,
            intent=intent,
            healed=False,
        )

    outcome = _match(db, order_reference=order_reference, amount_kobo=amount_kobo)

    settlement = LedgerSettlement(
        merchant_id=merchant_id,
        intent_id=outcome.intent.id if outcome.intent else None,
        invoice_id=outcome.intent.invoice_id if outcome.intent else None,
        order_reference=order_reference,
        transaction_ref=transaction_ref,
        amount=amount_kobo,
        source=source,
        status=outcome.status,
        raw_payload=raw_payload,
    )
    db.add(settlement)
    db.flush()

    healed = False
    if outcome.status == LedgerSettlementStatus.matched and outcome.intent:
        outcome.intent.status = LedgerIntentStatus.matched
        healed = _heal(db, intent=outcome.intent, settlement=settlement, now=now)

    elif outcome.status == LedgerSettlementStatus.anomaly and outcome.intent:
        outcome.intent.status = LedgerIntentStatus.anomaly
        log.warning(
            "ledger.matcher: drift intent=%d expected=%d got=%d order=%s",
            outcome.intent.id, outcome.intent.amount, amount_kobo, order_reference,
        )

    elif outcome.status == LedgerSettlementStatus.duplicate and outcome.intent:
        log.warning(
            "ledger.matcher: duplicate settlement for already-matched intent=%d order=%s",
            outcome.intent.id, order_reference,
        )

    elif outcome.status == LedgerSettlementStatus.orphan:
        # VA transfer path: attempt to match to an open invoice
        healed = _heal_orphan_va(db, settlement=settlement, raw_payload=raw_payload, now=now)

    log.info(
        "ledger.write_settlement: settlement=%d status=%s healed=%s order=%s tx=%s",
        settlement.id, outcome.status.value, healed, order_reference, transaction_ref,
    )
    return SettlementResult(
        settlement=settlement,
        status=outcome.status,
        intent=outcome.intent,
        healed=healed,
    )


# ---------------------------------------------------------------------------
# Matcher
# ---------------------------------------------------------------------------


@dataclass
class _MatchOutcome:
    status: LedgerSettlementStatus
    intent: LedgerIntent | None


def _match(db: Session, *, order_reference: str, amount_kobo: int) -> _MatchOutcome:
    intent = db.scalar(
        select(LedgerIntent).where(LedgerIntent.order_reference == order_reference)
    )

    if intent is None:
        return _MatchOutcome(status=LedgerSettlementStatus.orphan, intent=None)

    if intent.status == LedgerIntentStatus.matched:
        return _MatchOutcome(status=LedgerSettlementStatus.duplicate, intent=intent)

    delta = abs(intent.amount - amount_kobo)
    if delta > _AMOUNT_TOLERANCE_KOBO:
        return _MatchOutcome(status=LedgerSettlementStatus.anomaly, intent=intent)

    return _MatchOutcome(status=LedgerSettlementStatus.matched, intent=intent)


# ---------------------------------------------------------------------------
# Healing helpers
# ---------------------------------------------------------------------------


def _heal(
    db: Session,
    *,
    intent: LedgerIntent,
    settlement: LedgerSettlement,
    now: datetime,
) -> bool:
    """Mark invoice paid and advance subscription to active. Returns True on success."""
    invoice: Invoice | None = db.get(Invoice, intent.invoice_id)
    if invoice is None:
        return False

    invoice.status = InvoiceStatus.paid
    invoice.paid_at = now

    sub: Subscription | None = db.get(Subscription, intent.subscription_id)
    if sub is None:
        return False

    # Update ChargeAttempt if one exists
    if intent.charge_attempt_id:
        attempt: ChargeAttempt | None = db.get(ChargeAttempt, intent.charge_attempt_id)
        if attempt and attempt.status != ChargeAttemptStatus.succeeded:
            attempt.status = ChargeAttemptStatus.succeeded

    healable = {
        SubscriptionStatus.past_due,
        SubscriptionStatus.payment_uncertain,
        SubscriptionStatus.trialing,
    }
    if sub.status in healable:
        transition(
            sub,
            SubscriptionStatus.active,
            SubscriptionEventTrigger.reconciliation,
            db,
            metadata={"settlement_id": settlement.id, "invoice_id": invoice.id},
        )

    db.add(OutboxEvent(
        merchant_id=sub.merchant_id,
        aggregate_type="subscription",
        aggregate_id=str(sub.id),
        event_type="charge.succeeded",
        payload={
            "subscription_id": sub.id,
            "invoice_id": invoice.id,
            "amount": settlement.amount,
            "settlement_id": settlement.id,
            "source": settlement.source.value,
        },
        partition_key=str(sub.id),
        status=OutboxEventStatus.pending,
    ))
    return True


def _heal_orphan_va(
    db: Session,
    *,
    settlement: LedgerSettlement,
    raw_payload: dict[str, Any],
    now: datetime,
) -> bool:
    """Match a VA transfer to an open invoice by virtual-account number."""
    # Nomba transfer payloads carry the virtual-account number in the transaction data
    txn = raw_payload.get("data", {}).get("transaction", {})
    va_account_no: str = (
        txn.get("destinationAccountNumber")
        or txn.get("beneficiaryAccountNumber")
        or ""
    )
    if not va_account_no:
        log.info("ledger.orphan_va: no va_account_no in payload — cannot resolve")
        return False

    customer: Customer | None = db.scalar(
        select(Customer).where(Customer.va_account_no == va_account_no)
    )
    if customer is None:
        log.info("ledger.orphan_va: no customer for va_account_no=%s", va_account_no)
        return False

    open_invoice: Invoice | None = db.scalar(
        select(Invoice)
        .where(
            Invoice.customer_id == customer.id,
            Invoice.status == InvoiceStatus.open,
        )
        .order_by(Invoice.due_date)
        .limit(1)
    )
    if open_invoice is None:
        log.info("ledger.orphan_va: no open invoice for customer=%d", customer.id)
        return False

    # Backfill intent reference on the settlement
    settlement.invoice_id = open_invoice.id
    settlement.merchant_id = open_invoice.merchant_id
    settlement.status = LedgerSettlementStatus.matched

    open_invoice.status = InvoiceStatus.paid
    open_invoice.paid_at = now

    sub: Subscription | None = db.get(Subscription, open_invoice.subscription_id)
    if sub:
        healable = {SubscriptionStatus.past_due, SubscriptionStatus.payment_uncertain}
        if sub.status in healable:
            transition(
                sub,
                SubscriptionStatus.active,
                SubscriptionEventTrigger.transfer,
                db,
                metadata={"settlement_id": settlement.id, "va_account_no": va_account_no},
            )
        db.add(OutboxEvent(
            merchant_id=sub.merchant_id,
            aggregate_type="subscription",
            aggregate_id=str(sub.id),
            event_type="charge.succeeded",
            payload={
                "subscription_id": sub.id,
                "invoice_id": open_invoice.id,
                "amount": settlement.amount,
                "settlement_id": settlement.id,
                "source": settlement.source.value,
                "via": "va_transfer",
            },
            partition_key=str(sub.id),
            status=OutboxEventStatus.pending,
        ))

    log.info(
        "ledger.orphan_va: healed customer=%d invoice=%d via va=%s",
        customer.id, open_invoice.id, va_account_no,
    )
    return True
