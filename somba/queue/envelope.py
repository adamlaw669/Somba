"""Shared event envelope — the single message contract for the queue.

Every message on Redpanda is an EventEnvelope serialized to JSON bytes.
Producers build one, consumers parse one back. partition_key decides
ordering: same key → same partition → in-order processing.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


def _new_event_id() -> str:
    return uuid.uuid4().hex


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EventEnvelope:
    """One message on the queue. Mirrors the outbox_events row shape."""

    event_type: str          # e.g. "billing.due", "charge.succeeded"...you get the gist
    aggregate_type: str      # e.g. "subscription"
    aggregate_id: str        # e.g. the subscription id
    merchant_id: int         # tenant that owns this event
    partition_key: str       # routing key — subscription_id → in-order
    payload: dict            # event-specific body
    event_id: str = field(default_factory=_new_event_id)
    occurred_at: str = field(default_factory=_now_iso)
    version: int = 1

    def to_bytes(self) -> bytes:
        """Serialize for the wire."""
        return json.dumps(asdict(self)).encode("utf-8")

    @classmethod
    def from_bytes(cls, raw: bytes) -> "EventEnvelope":
        """Parse a message read off the queue back into an envelope."""
        return cls(**json.loads(raw.decode("utf-8")))

    def key_bytes(self) -> bytes:
        """Kafka message key — drives partition assignment."""
        return self.partition_key.encode("utf-8")
