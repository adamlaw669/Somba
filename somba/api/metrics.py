"""Operational metrics endpoint: key billing health counters for the merchant."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from somba.api.middleware.auth import get_current_merchant
from somba.db.models import (
    LedgerIntent,
    LedgerIntentStatus,
    Merchant,
    OutboxEvent,
    OutboxEventStatus,
    Subscription,
    SubscriptionEvent,
    SubscriptionStatus,
)
from somba.db.session import get_db

router = APIRouter(tags=["metrics"])


@router.get("/v1/metrics")
def get_metrics(
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    """Return key operational health counters for the authenticated merchant."""
    mid = merchant.id

    pending_intents = db.scalar(
        select(func.count()).select_from(LedgerIntent).where(
            LedgerIntent.status == LedgerIntentStatus.pending,
            LedgerIntent.merchant_id == mid,
        )
    )
    payment_uncertain = db.scalar(
        select(func.count()).select_from(Subscription).where(
            Subscription.status == SubscriptionStatus.payment_uncertain,
            Subscription.merchant_id == mid,
        )
    )
    outbox_pending = db.scalar(
        select(func.count()).select_from(OutboxEvent).where(
            OutboxEvent.status == OutboxEventStatus.pending,
            OutboxEvent.merchant_id == mid,
        )
    )
    active_subs = db.scalar(
        select(func.count()).select_from(Subscription).where(
            Subscription.status == SubscriptionStatus.active,
            Subscription.merchant_id == mid,
        )
    )

    # recovery_rate: of every time a subscription entered past_due, what
    # fraction eventually recovered back to active (healed by a settlement,
    # verify pass, or a later successful charge)?
    past_due_total = db.scalar(
        select(func.count()).select_from(SubscriptionEvent).where(
            SubscriptionEvent.to_status == SubscriptionStatus.past_due.value,
            SubscriptionEvent.merchant_id == mid,
        )
    )
    past_due_healed = db.scalar(
        select(func.count()).select_from(SubscriptionEvent).where(
            SubscriptionEvent.from_status == SubscriptionStatus.past_due.value,
            SubscriptionEvent.to_status == SubscriptionStatus.active.value,
            SubscriptionEvent.merchant_id == mid,
        )
    )
    recovery_rate = (past_due_healed / past_due_total) if past_due_total else None

    return {
        "metrics": {
            "pending_intents": pending_intents,
            "payment_uncertain_subscriptions": payment_uncertain,
            "outbox_pending_events": outbox_pending,
            "active_subscriptions": active_subs,
            "past_due_total": past_due_total,
            "past_due_healed": past_due_healed,
            "recovery_rate": recovery_rate,
        }
    }
