"""Subscription endpoints: create and list."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.api.errors import APIError
from somba.api.middleware.auth import get_current_merchant
from somba.db.models import (
    Customer,
    Merchant,
    OutboxEvent,
    OutboxEventStatus,
    Plan,
    PlanStatus,
    Subscription,
    SubscriptionEvent,
    SubscriptionEventTrigger,
    SubscriptionStatus,
)
from somba.db.session import get_db

router = APIRouter(prefix="/v1/subscriptions", tags=["subscriptions"])
log = logging.getLogger(__name__)

_INTERVAL_DAYS: dict[str, int] = {
    "day": 1,
    "week": 7,
    "month": 30,
    "year": 365,
}


def _next_period_end(interval: str, interval_count: int, start: datetime) -> datetime:
    days = _INTERVAL_DAYS.get(interval, 30) * interval_count
    return start + timedelta(days=days)


def _sub_to_dict(sub: Subscription) -> dict:
    return {
        "id": sub.id,
        "merchant_id": sub.merchant_id,
        "customer_id": sub.customer_id,
        "plan_id": sub.plan_id,
        "status": sub.status.value,
        "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "next_bill_date": sub.next_bill_date.isoformat() if sub.next_bill_date else None,
        "trial_end": sub.trial_end.isoformat() if sub.trial_end else None,
        "cancel_at_period_end": sub.cancel_at_period_end,
        "cancelled_at": sub.cancelled_at.isoformat() if sub.cancelled_at else None,
    }


class SubscriptionCreateRequest(BaseModel):
    plan_id: int
    customer_id: int
    trial_end: datetime | None = Field(
        default=None,
        description="Override the plan's trial period end. ISO 8601 UTC datetime.",
    )


@router.post("", status_code=201)
def create_subscription(
    body: SubscriptionCreateRequest,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    plan = db.scalar(
        select(Plan).where(Plan.id == body.plan_id, Plan.merchant_id == merchant.id)
    )
    if plan is None:
        raise APIError(code="not_found", message="Plan not found", status_code=404)
    if plan.status != PlanStatus.active:
        raise APIError(code="plan_archived", message="Plan is archived", status_code=400)

    customer = db.scalar(
        select(Customer).where(Customer.id == body.customer_id, Customer.merchant_id == merchant.id)
    )
    if customer is None:
        raise APIError(code="not_found", message="Customer not found", status_code=404)

    now = datetime.now(tz=timezone.utc)

    # Determine initial state and billing dates
    if body.trial_end is not None:
        trial_end = body.trial_end
        status = SubscriptionStatus.trialing
        period_start = now
        period_end = trial_end
        next_bill_date = trial_end
    elif plan.trial_days > 0:
        trial_end = now + timedelta(days=plan.trial_days)
        status = SubscriptionStatus.trialing
        period_start = now
        period_end = trial_end
        next_bill_date = trial_end
    else:
        trial_end = None
        status = SubscriptionStatus.active
        period_start = now
        period_end = _next_period_end(plan.interval, plan.interval_count, now)
        next_bill_date = now  # due immediately; sweep will pick it up

    sub = Subscription(
        merchant_id=merchant.id,
        customer_id=customer.id,
        plan_id=plan.id,
        status=status,
        current_period_start=period_start,
        current_period_end=period_end,
        next_bill_date=next_bill_date,
        trial_end=trial_end,
        cancel_at_period_end=False,
    )
    db.add(sub)
    db.flush()

    # Write the initial billing event (audit trail)
    db.add(SubscriptionEvent(
        subscription_id=sub.id,
        merchant_id=merchant.id,
        from_status="",
        to_status=status.value,
        trigger=SubscriptionEventTrigger.api,
        metadata_={"plan_id": plan.id, "customer_id": customer.id},
    ))

    # Publish subscription.created to outbox
    db.add(OutboxEvent(
        merchant_id=merchant.id,
        aggregate_type="subscription",
        aggregate_id=str(sub.id),
        event_type="subscription.created",
        payload={
            "subscription_id": sub.id,
            "customer_id": customer.id,
            "plan_id": plan.id,
            "status": status.value,
            "next_bill_date": next_bill_date.isoformat(),
        },
        partition_key=str(sub.id),
        status=OutboxEventStatus.pending,
    ))

    db.commit()
    db.refresh(sub)
    log.info(
        "subscriptions.create: sub=%d status=%s next_bill=%s merchant=%d",
        sub.id, status.value, next_bill_date.isoformat(), merchant.id,
    )
    return {"subscription": _sub_to_dict(sub)}


@router.get("")
def list_subscriptions(
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    subs = list(
        db.scalars(select(Subscription).where(Subscription.merchant_id == merchant.id))
    )
    return {"subscriptions": [_sub_to_dict(s) for s in subs]}


@router.get("/{subscription_id}")
def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    sub = db.scalar(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.merchant_id == merchant.id,
        )
    )
    if sub is None:
        raise APIError(code="not_found", message="Subscription not found", status_code=404)
    return {"subscription": _sub_to_dict(sub)}
