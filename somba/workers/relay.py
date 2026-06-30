"""Outbox relay: publish pending outbox events to the queue.

Polls outbox_events WHERE status='pending' ORDER BY id (the partial index
from migration 0003), publishes each via EventProducer, flushes to confirm
delivery, then marks them published. At-least-once: a crash after publish
but before the commit republishes on restart — consumer idempotency makes
that safe.
"""

from __future__ import annotations

import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.db.models import OutboxEvent, OutboxEventStatus
from somba.db.session import SessionLocal
from somba.queue.envelope import EventEnvelope
from somba.queue.producer import EventProducer

log = logging.getLogger(__name__)

_BATCH = 100


def _to_envelope(row: OutboxEvent) -> EventEnvelope:
    """Map a stored outbox row onto a queue envelope."""
    return EventEnvelope(
        event_type=row.event_type,
        aggregate_type=row.aggregate_type,
        aggregate_id=row.aggregate_id,
        merchant_id=row.merchant_id,
        partition_key=row.partition_key,
        payload=row.payload,
    )


def relay_pending(db: Session, producer: EventProducer, batch_size: int = _BATCH) -> int:
    """Publish one batch of pending events. Returns the number published."""
    rows = list(
        db.scalars(
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxEventStatus.pending)
            .order_by(OutboxEvent.id)
            .limit(batch_size)
        )
    )
    if not rows:
        return 0

    for row in rows:
        producer.publish(_to_envelope(row))

    # Confirm the broker accepted everything BEFORE marking done. If anything
    # is still undelivered, leave the whole batch pending and retry next pass.
    undelivered = producer.flush()
    if undelivered:
        log.error("relay: %d messages undelivered after flush; batch left pending", undelivered)
        return 0

    for row in rows:
        row.status = OutboxEventStatus.published
    db.commit()
    log.info("relay: published %d events", len(rows))
    return len(rows)


def run(poll_interval: float = 1.0) -> None:
    """Continuously drain the outbox. Sleeps only when there's nothing to do."""
    producer = EventProducer()
    log.info("relay started")
    while True:
        db = SessionLocal()
        try:
            published = relay_pending(db, producer)
        finally:
            db.close()
        if published == 0:
            time.sleep(poll_interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
