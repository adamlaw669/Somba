"""Observability alerts: surface the correctness risks the PRD demands.

- Pending ledger intents older than 10 min  -> "zero silent lost charges".
- payment_uncertain count stuck for 15 min  -> reconciliation worker is down.

Both are LOG-based: they emit an error-level line for a monitor/log drain to
fire on, and never mutate state.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from somba.db.models import (
    LedgerIntent,
    LedgerIntentStatus,
    Subscription,
    SubscriptionStatus,
)

log = logging.getLogger(__name__)

PENDING_INTENT_MAX_AGE_MINUTES = 10
PAYMENT_UNCERTAIN_STUCK_MINUTES = 15


def _as_utc(dt: datetime) -> datetime:
    """Treat a naive datetime (SQLite) as UTC so age math is tz-safe."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def check_pending_intents(
    db: Session,
    max_age_minutes: int = PENDING_INTENT_MAX_AGE_MINUTES,
    now: datetime | None = None,
) -> int:
    """Alert for every ledger intent stuck pending past max_age_minutes.

    Returns the count of stale intents. PRD rule: every intent must reach a
    terminal status; one pending >10m means a charge may be silently lost.
    """
    now = now or datetime.now(timezone.utc)
    pending = db.scalars(
        select(LedgerIntent).where(LedgerIntent.status == LedgerIntentStatus.pending)
    )

    stale = 0
    for intent in pending:
        if intent.created_at is None:
            continue
        age_min = (now - _as_utc(intent.created_at)).total_seconds() / 60
        if age_min >= max_age_minutes:
            stale += 1
            log.error(
                "ALERT unmatched_intent: id=%d sub=%d order_ref=%s pending %.1f min (>=%d)",
                intent.id, intent.subscription_id, intent.order_reference, age_min, max_age_minutes,
            )
    if stale:
        log.error("ALERT: %d ledger intent(s) pending >= %d min", stale, max_age_minutes)
    return stale


class PaymentUncertainMonitor:
    """Stateful monitor: alerts when the payment_uncertain count is stuck.

    A non-zero count that doesn't change for >= stuck_after_minutes means the
    reconciliation worker isn't draining payment_uncertain — i.e. it's down.
    Holds state across scheduler ticks, so keep ONE instance.
    """

    def __init__(self, stuck_after_minutes: int = PAYMENT_UNCERTAIN_STUCK_MINUTES) -> None:
        self._stuck_after = stuck_after_minutes
        self._last_count: int | None = None
        self._last_changed: datetime | None = None

    def check(self, db: Session, now: datetime | None = None) -> bool:
        """One observation. Returns True if it fired the stuck alert."""
        now = now or datetime.now(timezone.utc)
        count = db.scalar(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.status == SubscriptionStatus.payment_uncertain)
        )

        if count != self._last_count:
            # The count moved — recon is making progress. Reset the clock.
            self._last_count = count
            self._last_changed = now
            return False

        if count and self._last_changed is not None:
            stuck_min = (now - self._last_changed).total_seconds() / 60
            if stuck_min >= self._stuck_after:
                log.error(
                    "ALERT payment_uncertain_stuck: %d subscription(s) unchanged for %.1f min "
                    "(>=%d) — reconciliation worker may be down",
                    count, stuck_min, self._stuck_after,
                )
                return True
        return False
