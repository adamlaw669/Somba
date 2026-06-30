"""Queue configuration — broker address and topic names in one place."""

from __future__ import annotations

import os

# Broker address. The app container sets REDPANDA_BROKERS=redpanda:9092 (the
# internal listener). On the host, scripts/tests default to the external
# listener on port 19092 — see the dual-listener setup in docker-compose.yml.
BOOTSTRAP_SERVERS = os.getenv("REDPANDA_BROKERS", "localhost:19092")

# Single topic, partitioned by subscription_id. All billing/charge/recovery
# events flow through here. 12 partitions = up to 12 consumers in parallel,
# while same-subscription events stay ordered (same key → same partition).
EVENTS_TOPIC = "somba.events"
NUM_PARTITIONS = 12

# Single-node Redpanda in dev → one replica. (Prod would bump this.)
REPLICATION_FACTOR = 1
