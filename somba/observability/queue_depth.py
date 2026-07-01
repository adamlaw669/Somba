"""Queue depth: per-partition consumer lag on the billing events topic.

Lag = high watermark - committed offset. A lag that keeps growing means the
consumer group is falling behind (or is down) -- the delivery-side analogue
of the payment_uncertain alert on the billing side. LOG-based, like the other
alerts in this package: it never mutates state, just gives a monitor/log
drain something to graph and alert on.
"""

from __future__ import annotations

import logging

from confluent_kafka import Consumer, TopicPartition

from somba.queue.config import BOOTSTRAP_SERVERS, EVENTS_TOPIC

log = logging.getLogger(__name__)


def compute_lag(consumer, topic: str = EVENTS_TOPIC) -> dict[int, int]:
    """Compute and log per-partition lag for *consumer*'s group on *topic*.

    Split out from check_queue_depth so it can be exercised against a fake
    consumer in tests, without a live broker. consumer only needs
    list_topics/committed/get_watermark_offsets (the confluent_kafka.Consumer
    surface used here).
    """
    metadata = consumer.list_topics(topic, timeout=10)
    partitions = sorted(metadata.topics[topic].partitions.keys())
    tps = [TopicPartition(topic, p) for p in partitions]
    committed = consumer.committed(tps, timeout=10)

    lag_by_partition: dict[int, int] = {}
    total = 0
    for tp in committed:
        low, high = consumer.get_watermark_offsets(tp, timeout=10, cached=False)
        # No committed offset yet (-1001/OFFSET_INVALID) -> group hasn't started
        # consuming this partition; treat everything present as backlog.
        offset = tp.offset if tp.offset is not None and tp.offset >= 0 else low
        lag = max(0, high - offset)
        lag_by_partition[tp.partition] = lag
        total += lag
        log.info("queue_depth: topic=%s partition=%d lag=%d", topic, tp.partition, lag)

    log.info("queue_depth: topic=%s total_lag=%d", topic, total)
    return lag_by_partition


def check_queue_depth(
    group_id: str,
    topic: str = EVENTS_TOPIC,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
) -> dict[int, int]:
    """Connect to Kafka as *group_id* and log/return per-partition lag on *topic*."""
    consumer = Consumer(
        {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "enable.auto.commit": False,
        }
    )
    try:
        return compute_lag(consumer, topic)
    finally:
        consumer.close()
