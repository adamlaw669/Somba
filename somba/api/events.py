"""Outbox event read and replay endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.api.errors import APIError
from somba.api.middleware.auth import get_current_merchant
from somba.db.models import (
    Merchant,
    OutboxEvent,
    OutboxEventStatus,
    WebhookDelivery,
    WebhookDeliveryStatus,
)
from somba.db.session import get_db

router = APIRouter(prefix="/v1/events", tags=["events"])


def _event_to_dict(event: OutboxEvent) -> dict:
    return {
        "id": event.id,
        "event_type": event.event_type,
        "aggregate_type": event.aggregate_type,
        "aggregate_id": event.aggregate_id,
        "payload": event.payload,
        "status": event.status.value,
    }


@router.get("")
def list_events(
    event_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    stmt = (
        select(OutboxEvent)
        .where(OutboxEvent.merchant_id == merchant.id)
        .order_by(OutboxEvent.id.desc())
        .limit(200)
    )
    if event_type:
        stmt = stmt.where(OutboxEvent.event_type == event_type)
    if status:
        try:
            status_enum = OutboxEventStatus(status)
        except ValueError:
            raise APIError(code="invalid_param", message=f"Unknown status: {status}", status_code=400)
        stmt = stmt.where(OutboxEvent.status == status_enum)

    events = list(db.scalars(stmt))
    return {"events": [_event_to_dict(e) for e in events]}


@router.post("/{event_id}/replay", status_code=200)
def replay_event(
    event_id: int,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    event = db.scalar(
        select(OutboxEvent).where(
            OutboxEvent.id == event_id,
            OutboxEvent.merchant_id == merchant.id,
        )
    )
    if event is None:
        raise APIError(code="not_found", message="Event not found", status_code=404)

    # Reset the event so the emitter will re-deliver it
    event.status = OutboxEventStatus.pending

    # Reset any existing delivery record so the emitter creates a fresh attempt
    delivery: WebhookDelivery | None = db.scalar(
        select(WebhookDelivery).where(WebhookDelivery.outbox_event_id == event_id)
    )
    if delivery is not None:
        delivery.status = WebhookDeliveryStatus.pending
        delivery.attempt_count = 0
        delivery.next_retry_at = None

    db.commit()
    return {"replayed": True, "event_id": event_id}
