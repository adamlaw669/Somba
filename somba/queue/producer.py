"""Producer wrapper — publishes EventEnvelopes to Redpanda.

Keys every message by partition_key (the subscription_id) so all events for
one subscription land on the same partition and stay ordered.
"""

from __future__ import annotations

import logging

from confluent_kafka import Producer

from somba.queue.config import BOOTSTRAP_SERVERS, EVENTS_TOPIC
from somba.queue.envelope import EventEnvelope

logger = logging.getLogger(__name__)


class EventProducer:
    """Thin wrapper over confluent_kafka.Producer for Somba envelopes."""

    def __init__(self, bootstrap_servers: str = BOOTSTRAP_SERVERS) -> None:
        self._producer = Producer(
            {
                "bootstrap.servers": bootstrap_servers,
                # Don't lose messages on a broker hiccup: wait for all
                # in-sync replicas to ack before considering a send done.
                "acks": "all",
                # Safe retries without reordering or duplicating on the wire.
                "enable.idempotence": True,
            }
        )

    def _on_delivery(self, err, msg) -> None:
        """Called once per message when the broker acks (or fails) it."""
        if err is not None:
            logger.error("delivery failed for key=%s: %s", msg.key(), err)
        else:
            logger.debug(
                "delivered to %s[%s]@%s", msg.topic(), msg.partition(), msg.offset()
            )

    def publish(self, envelope: EventEnvelope, topic: str = EVENTS_TOPIC) -> None:
        """Queue an envelope for delivery. Key = partition_key → ordering."""
        self._producer.produce(
            topic=topic,
            key=envelope.key_bytes(),
            value=envelope.to_bytes(),
            on_delivery=self._on_delivery,
        )
        # poll(0) services delivery callbacks without blocking.
        self._producer.poll(0)

    def flush(self, timeout: float = 10.0) -> int:
        """Block until all queued messages are delivered. Returns # still pending."""
        return self._producer.flush(timeout)
