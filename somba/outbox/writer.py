"""Transactional outbox writer.

Adds an outbox event to the CALLER's session so it commits atomically with
the business change in the same transaction. Does NOT commit — the caller
owns the transaction boundary. The relay publishes pending rows later.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from somba.db.models import OutboxEvent, OutboxEventStatus


def write_event(
    db: Session,
    *,
    merchant_id: int,
    aggregate_type: str,
    aggregate_id: str | int,
    event_type: str,
    payload: dict[str, Any],
    partition_key: str | None = None,
) -> OutboxEvent:
    """Stage an outbox event in the caller's transaction.

    partition_key defaults to aggregate_id, so events for one subscription
    share a partition and stay ordered (matches EventProducer keying).
    Returns the staged row; the caller commits.
    """
    event = OutboxEvent(
        merchant_id=merchant_id,
        aggregate_type=aggregate_type,
        aggregate_id=str(aggregate_id),
        event_type=event_type,
        payload=payload,
        partition_key=partition_key or str(aggregate_id),
        status=OutboxEventStatus.pending,
    )
    db.add(event)
    return event
