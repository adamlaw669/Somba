"""Subscription endpoints: create, list, get, and plan-change with proration."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.api.errors import APIError
from somba.api.middleware.auth import get_current_merchant
from somba.db.models import (
    Customer,
    Invoice,
    InvoiceLineItem,
    InvoiceLineItemType,
    InvoiceStatus,
    InvoiceType,
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
from somba.subscriptions.proration import calculate as calc_proration
from somba.workers.reconcile.writer import write_intent

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


class SubscriptionPatchRequest(BaseModel):
    plan_id: int = Field(description="New plan to switch to.")


@router.patch("/{subscription_id}")
def change_plan(
    subscription_id: int,
    body: SubscriptionPatchRequest,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    """Change a subscription's plan mid-cycle with proration.

    Upgrade (net > 0): creates an immediate proration invoice + ledger intent.
    Downgrade (net ≤ 0): stores the credit in customer.credit_balance.
    In both cases the subscription's plan_id is updated and a SubscriptionEvent
    and OutboxEvent are written.
    """
    sub = db.scalar(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.merchant_id == merchant.id,
        )
    )
    if sub is None:
        raise APIError(code="not_found", message="Subscription not found", status_code=404)

    if sub.status not in (SubscriptionStatus.active, SubscriptionStatus.trialing):
        raise APIError(
            code="invalid_status",
            message=f"Cannot change plan on a subscription in status '{sub.status.value}'",
            status_code=400,
        )

    if sub.plan_id == body.plan_id:
        raise APIError(code="no_change", message="Subscription is already on that plan", status_code=400)

    new_plan = db.scalar(
        select(Plan).where(Plan.id == body.plan_id, Plan.merchant_id == merchant.id)
    )
    if new_plan is None:
        raise APIError(code="not_found", message="Plan not found", status_code=404)
    if new_plan.status != PlanStatus.active:
        raise APIError(code="plan_archived", message="Plan is archived", status_code=400)

    old_plan: Plan = db.get(Plan, sub.plan_id)
    now = datetime.now(tz=timezone.utc)

    period_start = sub.current_period_start or now
    period_end = sub.current_period_end or now

    proration = calc_proration(
        old_plan_amount=old_plan.amount,
        new_plan_amount=new_plan.amount,
        period_start=period_start,
        period_end=period_end,
        change_date=now,
    )

    customer: Customer = db.get(Customer, sub.customer_id)

    if proration.net_kobo > 0:
        # Upgrade: bill the difference immediately
        proration_invoice = Invoice(
            merchant_id=merchant.id,
            subscription_id=sub.id,
            customer_id=sub.customer_id,
            amount=proration.net_kobo,
            status=InvoiceStatus.open,
            type=InvoiceType.proration,
            period_start=now,
            period_end=period_end,
            due_date=now,
        )
        db.add(proration_invoice)
        db.flush()

        # Credit line item
        db.add(InvoiceLineItem(
            invoice_id=proration_invoice.id,
            merchant_id=merchant.id,
            type=InvoiceLineItemType.proration_credit,
            description=f"Unused value: {old_plan.name} ({proration.remaining_days} days)",
            amount=-proration.credit_kobo,
            period_start=now,
            period_end=period_end,
        ))
        # Charge line item
        db.add(InvoiceLineItem(
            invoice_id=proration_invoice.id,
            merchant_id=merchant.id,
            type=InvoiceLineItemType.proration_charge,
            description=f"Upgrade to: {new_plan.name} ({proration.remaining_days} days)",
            amount=proration.charge_kobo,
            period_start=now,
            period_end=period_end,
        ))

        order_reference = f"order-{uuid.uuid4().hex}"
        billing_period = now.date()
        idem_key = f"proration_{sub.id}_{billing_period.isoformat()}_1"

        # Apply any available credit balance first
        net_after_credit = max(0, proration.net_kobo - customer.credit_balance)
        if customer.credit_balance > 0:
            applied = min(customer.credit_balance, proration.net_kobo)
            customer.credit_balance -= applied

        if net_after_credit > 0:
            write_intent(
                db,
                merchant_id=merchant.id,
                subscription_id=sub.id,
                invoice_id=proration_invoice.id,
                order_reference=order_reference,
                amount=net_after_credit,
                idempotency_key=idem_key,
            )
        else:
            # Fully covered by existing credit — mark invoice paid immediately
            proration_invoice.status = InvoiceStatus.paid
            proration_invoice.paid_at = now

        proration_action = "charge"

    else:
        # Downgrade: credit the customer
        credit = abs(proration.net_kobo)
        if credit > 0:
            customer.credit_balance += credit

        # Record a zero-amount proration invoice for the audit trail
        proration_invoice = Invoice(
            merchant_id=merchant.id,
            subscription_id=sub.id,
            customer_id=sub.customer_id,
            amount=0,
            status=InvoiceStatus.paid,
            type=InvoiceType.proration,
            period_start=now,
            period_end=period_end,
            due_date=now,
            paid_at=now,
        )
        db.add(proration_invoice)
        db.flush()

        db.add(InvoiceLineItem(
            invoice_id=proration_invoice.id,
            merchant_id=merchant.id,
            type=InvoiceLineItemType.proration_credit,
            description=f"Downgrade credit: {old_plan.name} → {new_plan.name} ({proration.remaining_days} days)",
            amount=credit,
            period_start=now,
            period_end=period_end,
        ))

        proration_action = "credit"

    old_plan_id = sub.plan_id
    sub.plan_id = new_plan.id

    # Audit trail
    db.add(SubscriptionEvent(
        subscription_id=sub.id,
        merchant_id=merchant.id,
        from_status=sub.status.value,
        to_status=sub.status.value,
        trigger=SubscriptionEventTrigger.api,
        metadata_={
            "old_plan_id": old_plan_id,
            "new_plan_id": new_plan.id,
            "proration_action": proration_action,
            "net_kobo": proration.net_kobo,
            "credit_kobo": proration.credit_kobo,
            "charge_kobo": proration.charge_kobo,
        },
    ))

    db.add(OutboxEvent(
        merchant_id=merchant.id,
        aggregate_type="subscription",
        aggregate_id=str(sub.id),
        event_type="subscription.plan_changed",
        payload={
            "subscription_id": sub.id,
            "old_plan_id": old_plan_id,
            "new_plan_id": new_plan.id,
            "proration_action": proration_action,
            "net_kobo": proration.net_kobo,
        },
        partition_key=str(sub.id),
        status=OutboxEventStatus.pending,
    ))

    db.commit()
    db.refresh(sub)
    log.info(
        "subscriptions.patch: sub=%d %d→%d proration=%s net=%d",
        sub.id, old_plan_id, new_plan.id, proration_action, proration.net_kobo,
    )
    return {
        "subscription": _sub_to_dict(sub),
        "proration": {
            "action": proration_action,
            "credit_kobo": proration.credit_kobo,
            "charge_kobo": proration.charge_kobo,
            "net_kobo": proration.net_kobo,
            "remaining_days": proration.remaining_days,
            "total_days": proration.total_days,
        },
    }
