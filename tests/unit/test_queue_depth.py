"""queue_depth: per-partition consumer lag, computed against a fake consumer
so this runs without a live Kafka/Redpanda broker."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from somba.observability.queue_depth import compute_lag

TOPIC = "somba.events"


@dataclass
class _FakeTopicMeta:
    partitions: dict[int, object]


@dataclass
class _FakeClusterMeta:
    topics: dict[str, _FakeTopicMeta]


@dataclass
class _FakeTP:
    topic: str
    partition: int
    offset: int


class _FakeConsumer:
    """Stands in for confluent_kafka.Consumer's read-only metadata surface."""

    def __init__(self, num_partitions: int, committed_offsets: dict[int, int], watermarks: dict[int, tuple[int, int]]):
        self._num_partitions = num_partitions
        self._committed_offsets = committed_offsets
        self._watermarks = watermarks

    def list_topics(self, topic, timeout=10):
        return _FakeClusterMeta(
            topics={topic: _FakeTopicMeta(partitions={p: None for p in range(self._num_partitions)})}
        )

    def committed(self, tps, timeout=10):
        return [_FakeTP(tp.topic, tp.partition, self._committed_offsets.get(tp.partition, -1001)) for tp in tps]

    def get_watermark_offsets(self, tp, timeout=10, cached=False):
        return self._watermarks[tp.partition]


def test_compute_lag_returns_per_partition_backlog(caplog):
    consumer = _FakeConsumer(
        num_partitions=2,
        committed_offsets={0: 100, 1: 50},
        watermarks={0: (0, 130), 1: (0, 50)},
    )

    with caplog.at_level(logging.INFO, logger="somba.observability.queue_depth"):
        lag = compute_lag(consumer, topic=TOPIC)

    assert lag == {0: 30, 1: 0}
    assert any("total_lag=30" in r.message for r in caplog.records)


def test_compute_lag_treats_no_committed_offset_as_full_backlog():
    """Group never consumed this partition (offset invalid) -> everything present is lag."""
    consumer = _FakeConsumer(
        num_partitions=1,
        committed_offsets={},  # no entry -> OFFSET_INVALID (-1001)
        watermarks={0: (0, 42)},
    )

    lag = compute_lag(consumer, topic=TOPIC)

    assert lag == {0: 42}


def test_compute_lag_never_negative_when_committed_ahead_of_high_watermark():
    """Defensive: a stale watermark read should not report negative lag."""
    consumer = _FakeConsumer(
        num_partitions=1,
        committed_offsets={0: 100},
        watermarks={0: (0, 90)},
    )

    lag = compute_lag(consumer, topic=TOPIC)

    assert lag == {0: 0}
