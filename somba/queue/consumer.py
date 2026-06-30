"""Consumer base class — at-least-once delivery via commit-after-write.

Subclasses implement handle(envelope). The base loop reads a message, runs
handle(), and ONLY commits the offset if handle() succeeded. A crash before
commit means the message is redelivered on restart — nothing is lost.
Idempotency keys downstream make redelivery safe.
"""

from __future__ import annotations

import logging

from confluent_kafka import Consumer, KafkaError

from somba.queue.config import BOOTSTRAP_SERVERS, EVENTS_TOPIC
from somba.queue.envelope import EventEnvelope

logger = logging.getLogger(__name__)


class EventConsumer:
    """Base consumer. Subclass and implement handle()."""

    def __init__(
        self,
        group_id: str,
        topic: str = EVENTS_TOPIC,
        bootstrap_servers: str = BOOTSTRAP_SERVERS,
    ) -> None:
        self._consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                # All consumers sharing a group_id split the partitions
                # between them — that's how we scale horizontally.
                "group.id": group_id,
                # New group with no committed offset starts at the beginning.
                "auto.offset.reset": "earliest",
                # The crux: WE commit, not the client library. Commit only
                # happens after handle() returns successfully.
                "enable.auto.commit": False,
            }
        )
        self._topic = topic
        self._running = False

    def handle(self, envelope: EventEnvelope) -> None:
        """Process one event. Override in subclasses. Raise to NOT commit."""
        raise NotImplementedError

    def run(self) -> None:
        """Poll → handle → commit loop. Blocks until stop() is called."""
        self._consumer.subscribe([self._topic])
        self._running = True
        try:
            while self._running:
                msg = self._consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    # Partition EOF is informational, not a real error.
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error("consume error: %s", msg.error())
                    continue

                try:
                    envelope = EventEnvelope.from_bytes(msg.value())
                    self.handle(envelope)
                except Exception:  # noqa: BLE001
                    # Do NOT commit — message will be redelivered. Log and
                    # move on so one poison message doesn't wedge the loop.
                    logger.exception("handle failed; offset not committed")
                    continue

                # Commit ONLY after a successful handle → at-least-once.
                self._consumer.commit(msg, asynchronous=False)
        finally:
            self._consumer.close()

    def stop(self) -> None:
        self._running = False
