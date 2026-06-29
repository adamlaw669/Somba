"""Subscription state machine: exhaustive transition table with audit events."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from somba.db.models import (
    Subscription,
    SubscriptionEvent,
    SubscriptionEventTrigger,
    SubscriptionStatus,
)

log = logging.getLogger(__name__)

# Every state must appear as a key; terminal states map to an empty frozenset.
VALID_TRANSITIONS: dict[SubscriptionStatus, frozenset[SubscriptionStatus]] = {
    SubscriptionStatus.trialing: frozenset({
        SubscriptionStatus.active,
        SubscriptionStatus.past_due,
        SubscriptionStatus.cancelled,
        SubscriptionStatus.expired,
    }),
    SubscriptionStatus.active: frozenset({
        SubscriptionStatus.past_due,
        SubscriptionStatus.paused,
        SubscriptionStatus.cancelled,
        SubscriptionStatus.expired,
    }),
    SubscriptionStatus.past_due: frozenset({
        SubscriptionStatus.active,
        SubscriptionStatus.payment_uncertain,
        SubscriptionStatus.cancelled,
        SubscriptionStatus.expired,
    }),
    SubscriptionStatus.payment_uncertain: frozenset({
        SubscriptionStatus.active,
        SubscriptionStatus.past_due,
        SubscriptionStatus.cancelled,
    }),
    SubscriptionStatus.paused: frozenset({
        SubscriptionStatus.active,
        SubscriptionStatus.cancelled,
        SubscriptionStatus.expired,
    }),
    SubscriptionStatus.cancelled: frozenset(),
    SubscriptionStatus.expired: frozenset(),
}

# Verify the table is exhaustive at import time.
assert set(VALID_TRANSITIONS) == set(SubscriptionStatus), (
    "VALID_TRANSITIONS is missing states — update the table when adding new SubscriptionStatus values"
)


class IllegalTransitionError(ValueError):
    """Raised when a requested state transition is not in the transition table."""


def transition(
    sub: Subscription,
    to_status: SubscriptionStatus,
    trigger: SubscriptionEventTrigger,
    db: Session,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Apply a state transition, write the audit event row, or raise on illegal moves.

    Raises IllegalTransitionError (and logs at ERROR level) for any move not
    listed in VALID_TRANSITIONS. The subscription row and the audit event are
    both added to *db* but not committed — the caller owns the transaction.
    """
    from_status = sub.status
    allowed = VALID_TRANSITIONS[from_status]

    if to_status not in allowed:
        msg = (
            f"Illegal transition sub={sub.id}: "
            f"{from_status.value!r} → {to_status.value!r} "
            f"(trigger={trigger.value})"
        )
        log.error(msg)
        raise IllegalTransitionError(msg)

    sub.status = to_status

    db.add(
        SubscriptionEvent(
            subscription_id=sub.id,
            merchant_id=sub.merchant_id,
            from_status=from_status.value,
            to_status=to_status.value,
            trigger=trigger,
            metadata_=metadata or {},
        )
    )

    log.info(
        "sub.transition sub=%d %s→%s trigger=%s",
        sub.id,
        from_status.value,
        to_status.value,
        trigger.value,
    )
