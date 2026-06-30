"""Create the Redpanda topic(s) Somba needs. Safe to run repeatedly."""

from __future__ import annotations

import sys

from confluent_kafka.admin import AdminClient, NewTopic

from somba.queue.config import (
    BOOTSTRAP_SERVERS,
    EVENTS_TOPIC,
    NUM_PARTITIONS,
    REPLICATION_FACTOR,
)


def create_topics() -> None:
    admin = AdminClient({"bootstrap.servers": BOOTSTRAP_SERVERS})

    topic = NewTopic(
        EVENTS_TOPIC,
        num_partitions=NUM_PARTITIONS,
        replication_factor=REPLICATION_FACTOR,
    )

    # create_topics returns a dict: {topic_name: Future}. We wait on each.
    futures = admin.create_topics([topic])

    for name, future in futures.items():
        try:
            future.result()  # blocks until the broker answers
            print(f"created topic '{name}' ({NUM_PARTITIONS} partitions)")
        except Exception as exc:  # noqa: BLE001
            # Already-exists is fine — this script must be idempotent.
            if "already exists" in str(exc).lower():
                print(f"topic '{name}' already exists — skipping")
            else:
                print(f"failed to create '{name}': {exc}", file=sys.stderr)
                raise


if __name__ == "__main__":
    print(f"connecting to {BOOTSTRAP_SERVERS} ...")
    create_topics()
