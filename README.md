# Somba

Somba is recurring-billing and recovery infrastructure built on top of Nomba's payment rails.

It is meant for businesses and product teams that want to offer subscriptions, retries, proration, recovery, customer self-service, and reconciliation without building the whole billing system themselves.

The short version: Somba is Stripe Billing for Nomba, with recovery logic designed for Nigerian payment behavior.

## Why it exists

Recurring billing is easy to describe and hard to run well. Real-world payments fail for different reasons, some of which are temporary and some of which need a different recovery path entirely.

Somba is designed to keep subscriptions alive when possible, avoid double charges, and make every naira traceable.

## Start here

- Read the product requirements in [PRD.md](./PRD.md)
- Read the product overview in [docs/overview.md](./docs/overview.md)
- Read the architecture guide in [docs/architecture.md](./docs/architecture.md)
- Read the subscription lifecycle in [docs/state-machine.md](./docs/state-machine.md)
- Read the recovery logic in [docs/recovery-engine.md](./docs/recovery-engine.md)

## Architecture image

The system diagram is stored at [docs/assets/architecture.png](./docs/assets/architecture.png).

It shows the entry points, the outbox, relay shards, event queues, workers, the state machine, the ledger, and the merchant/Nomba touchpoints.

## Documentation index

- [Overview](./docs/overview.md)
- [Architecture](./docs/architecture.md)
- [State Machine](./docs/state-machine.md)
- [Recovery Engine](./docs/recovery-engine.md)
- [Reconciliation](./docs/reconciliation.md)
- [API Reference](./docs/api-reference.md)
- [Data Model](./docs/data-model.md)
- [Proration](./docs/proration.md)
- [NFRs](./docs/nfrs.md)
- [Getting Started](./docs/getting-started.md)

## What is in this repo

- [PRD.md](./PRD.md) describes the product in plain English
- [docs/](./docs/) contains the supporting documentation pages
- [somba/](./somba/) is the placeholder Python package structure
- [tests/](./tests/) is the placeholder test structure
- [scripts/](./scripts/) contains developer helper stubs

## Notes

This repository is still at scaffold stage. The current files are documentation and placeholders only, so the next step is implementation once the product shape is finalized.

> Somba by Team setld
