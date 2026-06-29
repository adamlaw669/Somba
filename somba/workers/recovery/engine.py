"""Recovery engine: select the next action after a charge failure.

Decision table
--------------
empty_account  → timing path  (retry at a better funding window)
transient      → timing path  (retry once quickly, then back off)
broken_card    → transfer path (stop pulling; ask for a push transfer)
risk           → transfer path (stop immediately; do not re-attempt)
unknown        → timing path  (bounded, conservative retry)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy.orm import Session

from somba.db.models import (
    FailureClass,
    OutboxEvent,
    OutboxEventStatus,
    RecoverySchedule,
    RecoveryScheduleReasonClass,
    RecoveryScheduleStatus,
)

log = logging.getLogger(__name__)

# Delay offsets per attempt on the timing path (in hours).
_TIMING_DELAYS_HOURS: dict[FailureClass, list[float]] = {
    FailureClass.empty_account: [4, 24, 72],    # try near payday-adjacent windows
    FailureClass.transient: [0.5, 4, 24],        # shorter initial gap; soft declines clear fast
    FailureClass.unknown: [8, 48, 96],           # conservative
}

Action = Literal["timing", "transfer"]


def _timing_delay(failure_class: FailureClass, attempt_number: int) -> timedelta:
    schedule = _TIMING_DELAYS_HOURS.get(failure_class, [8, 48, 96])
    idx = min(attempt_number - 1, len(schedule) - 1)
    return timedelta(hours=schedule[idx])


def run(
    db: Session,
    *,
    merchant_id: int,
    subscription_id: int,
    invoice_id: int,
    charge_attempt_id: int,
    failure_class: FailureClass,
    attempt_number: int,
    now: datetime | None = None,
) -> Action:
    """Decide and execute the recovery action.

    Writes a RecoverySchedule row on the timing path or an OutboxEvent on
    the transfer path. The caller owns the DB transaction (no commit here).
    Returns the action taken for observability.
    """
    now = now or datetime.now(tz=timezone.utc)
    action = _select_action(failure_class, attempt_number)

    if action == "timing":
        scheduled_for = now + _timing_delay(failure_class, attempt_number)
        db.add(RecoverySchedule(
            merchant_id=merchant_id,
            subscription_id=subscription_id,
            invoice_id=invoice_id,
            charge_attempt_id=charge_attempt_id,
            scheduled_for=scheduled_for,
            reason_class=RecoveryScheduleReasonClass(failure_class.value),
            attempt_number=attempt_number + 1,
            status=RecoveryScheduleStatus.scheduled,
        ))
        log.info(
            "recovery.engine: timing path sub=%d attempt=%d scheduled_for=%s",
            subscription_id,
            attempt_number,
            scheduled_for.isoformat(),
        )

    else:  # transfer
        db.add(OutboxEvent(
            merchant_id=merchant_id,
            aggregate_type="subscription",
            aggregate_id=str(subscription_id),
            event_type="subscription.transfer_required",
            payload={
                "subscription_id": subscription_id,
                "invoice_id": invoice_id,
                "charge_attempt_id": charge_attempt_id,
                "failure_class": failure_class.value,
            },
            partition_key=str(subscription_id),
            status=OutboxEventStatus.pending,
        ))
        log.info(
            "recovery.engine: transfer path sub=%d failure_class=%s",
            subscription_id,
            failure_class.value,
        )

    return action


def _select_action(failure_class: FailureClass, attempt_number: int) -> Action:
    """Return 'timing' or 'transfer' based on class and attempt history."""
    if failure_class in (FailureClass.broken_card, FailureClass.risk):
        return "transfer"
    # transient: give one timing retry, then switch to transfer
    if failure_class == FailureClass.transient and attempt_number >= 2:
        return "transfer"
    return "timing"
