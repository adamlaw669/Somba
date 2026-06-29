"""Billing sweep: find subscriptions due for charge and manage billing locks."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from somba.db.models import (
    BillingLock,
    BillingLockStatus,
    Subscription,
    SubscriptionStatus,
)

log = logging.getLogger(__name__)

_BILLABLE_STATUSES = (SubscriptionStatus.active, SubscriptionStatus.trialing)
_SWEEP_LIMIT = 500


def fetch_due_subscriptions(
    db: Session,
    cutoff: datetime | None = None,
    limit: int = _SWEEP_LIMIT,
) -> list[Subscription]:
    """Return subscriptions whose next_bill_date is on or before *cutoff*.

    Uses the composite index ix_subscriptions_status_next_bill_date.
    """
    cutoff = cutoff or datetime.now(tz=timezone.utc)
    return list(
        db.scalars(
            select(Subscription)
            .where(
                Subscription.status.in_(_BILLABLE_STATUSES),
                Subscription.next_bill_date <= cutoff,
            )
            .order_by(Subscription.next_bill_date)
            .limit(limit)
        )
    )


def acquire_billing_lock(
    db: Session,
    subscription_id: int,
    billing_period: object,  # datetime.date
) -> bool:
    """Claim the billing lock for (subscription_id, billing_period).

    Implements INSERT ON CONFLICT DO NOTHING semantics via a nested
    transaction (SAVEPOINT). Returns True when the lock is newly acquired,
    False when it already existed.
    """
    try:
        with db.begin_nested():
            db.add(
                BillingLock(
                    subscription_id=subscription_id,
                    billing_period=billing_period,
                    status=BillingLockStatus.locked,
                )
            )
            db.flush()
        return True
    except IntegrityError:
        log.debug(
            "billing_lock: already held sub=%d period=%s",
            subscription_id,
            billing_period,
        )
        return False
