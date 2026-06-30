"""Outbound webhook emitter: signs and delivers OutboxEvents to merchant URLs."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.db.models import (
    Merchant,
    OutboxEvent,
    OutboxEventStatus,
    WebhookDelivery,
    WebhookDeliveryStatus,
)

log = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
# Retry delays in seconds: 30s, 60s, 120s (exponential)
_RETRY_DELAYS = [30, 60, 120]


def run(db: Session, *, now: datetime | None = None, limit: int = 100) -> int:
    """Process pending OutboxEvents and deliver them to merchant webhook URLs.

    Returns the number of delivery attempts made.
    """
    now = now or datetime.now(tz=timezone.utc)

    events: list[OutboxEvent] = list(
        db.scalars(
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxEventStatus.pending)
            .order_by(OutboxEvent.id)
            .limit(limit)
        )
    )
    log.info("emitter: %d pending events", len(events))

    attempted = 0
    for event in events:
        merchant: Merchant | None = db.get(Merchant, event.merchant_id)
        if merchant is None or not merchant.webhook_url:
            # No delivery target — mark published so we don't re-process
            event.status = OutboxEventStatus.published
            db.commit()
            continue

        delivery = _get_or_create_delivery(db, event, merchant, now)
        if delivery is None:
            continue  # already delivered or permanently failed

        _attempt_delivery(db, event, delivery, merchant, now)
        attempted += 1

    return attempted


def _get_or_create_delivery(
    db: Session,
    event: OutboxEvent,
    merchant: Merchant,
    now: datetime,
) -> WebhookDelivery | None:
    delivery: WebhookDelivery | None = db.scalar(
        select(WebhookDelivery).where(WebhookDelivery.outbox_event_id == event.id)
    )

    if delivery is None:
        body = _build_body(event, now)
        sig = _sign(merchant.webhook_secret, body)
        delivery = WebhookDelivery(
            merchant_id=merchant.id,
            outbox_event_id=event.id,
            event_type=event.event_type,
            payload=body,
            signature=sig,
            status=WebhookDeliveryStatus.pending,
            attempt_count=0,
        )
        db.add(delivery)
        db.flush()
        return delivery

    if delivery.status == WebhookDeliveryStatus.delivered:
        return None

    if delivery.status == WebhookDeliveryStatus.failed:
        return None

    # pending — check if we should retry yet
    if delivery.next_retry_at and now < delivery.next_retry_at:
        return None

    return delivery


def _attempt_delivery(
    db: Session,
    event: OutboxEvent,
    delivery: WebhookDelivery,
    merchant: Merchant,
    now: datetime,
) -> None:
    delivery.attempt_count += 1
    body = delivery.payload
    sig = delivery.signature

    try:
        import httpx

        with httpx.Client(timeout=10) as client:
            resp = client.post(
                merchant.webhook_url,
                json=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Somba-Signature": f"sha256={sig}",
                    "X-Somba-Event": event.event_type,
                    "X-Somba-Event-Id": str(event.id),
                },
            )
        status_code = resp.status_code
        success = 200 <= status_code < 300

    except Exception as exc:
        log.warning("emitter: delivery error event=%d: %s", event.id, exc)
        status_code = 0
        success = False

    delivery.last_response_status = status_code

    if success:
        delivery.status = WebhookDeliveryStatus.delivered
        event.status = OutboxEventStatus.published
        log.info("emitter: delivered event=%d attempt=%d", event.id, delivery.attempt_count)
    else:
        if delivery.attempt_count >= _MAX_ATTEMPTS:
            delivery.status = WebhookDeliveryStatus.failed
            # Do NOT mark event published — leave for manual replay
            log.warning(
                "emitter: permanently failed event=%d after %d attempts",
                event.id,
                delivery.attempt_count,
            )
        else:
            delay = _RETRY_DELAYS[delivery.attempt_count - 1] if delivery.attempt_count <= len(_RETRY_DELAYS) else 120
            delivery.next_retry_at = now + timedelta(seconds=delay)
            log.info(
                "emitter: will retry event=%d attempt=%d in %ds",
                event.id,
                delivery.attempt_count,
                delay,
            )

    db.commit()


def _build_body(event: OutboxEvent, now: datetime) -> dict[str, Any]:
    return {
        "event_type": event.event_type,
        "event_id": event.id,
        "timestamp": now.isoformat(),
        "data": event.payload,
    }


def _sign(secret: str, body: dict[str, Any]) -> str:
    """HMAC-SHA256 signature of the JSON body, hex-encoded."""
    payload_bytes = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
