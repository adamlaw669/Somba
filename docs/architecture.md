# Architecture

This page describes the full system layout, the main components, and how events move through Somba from billing due dates to external payment services.

## System overview

Somba is built as a modular monolith. That means it is one application boundary, but the code is split into clear internal modules so billing, recovery, reconciliation, and API handling stay separate in practice.

The important idea is that every major action happens through a controlled flow: something becomes due, an event is recorded, workers process it, and the resulting state is stored for later proof.

## Entry points

There are four main entry points into the system:

- Developers using the public API
- Customers using the customer portal
- Nomba webhooks arriving from external payment activity
- The scheduler, which wakes up on time-based rules

Each entry point feeds the same billing system so Somba does not have one logic path for "manual" work and another for "automated" work.

## Event flow

The flow is intentionally boring and repeatable:

1. A bill becomes due or a web event arrives.
2. Somba records the intent or fact in the database first.
3. The event is put into the outbox.
4. The relay publishes the event into the queue.
5. A worker picks up the event and decides what happens next.
6. The subscription state and ledger are updated.
7. If needed, Somba emits a webhook to the merchant.

This separation matters because billing is safer when "remembering" something and "acting on it" are not the same step.

## Queue shards and relay

The architecture image uses queue shard labels such as `S0`, `S1`, `S2`, and `S3` to show that events are partitioned and processed in order per subscription. The point of those shards is not speed alone; it is order.

If two events for the same subscription arrive close together, they must be handled in sequence so the system never charges, pauses, or heals the same subscription out of order.

The `outbox` stores events before they are published, and the `relay` publishes them into the event queues so work is not lost if a process stops in the middle. This is the "do not lose the message" safety net.

## State machine

The subscription state machine is the business truth. It decides which state changes are legal and which ones must be rejected.

Examples:

- A successful charge can move a subscription back to `active`
- A timeout can move it to `payment_uncertain`
- A pause request can move it to `paused`
- A cancelled subscription should not silently become active again without a deliberate recovery event

The state machine prevents accidental transitions that would confuse both the merchant and the customer.

## Ledger

The ledger is the proof layer. It records what Somba intended to do and what Nomba or the transfer rail actually confirmed.

That gives Somba a way to answer the hard questions:

- Did we try to charge this customer?
- Did the charge succeed?
- Did the merchant already get credit?
- Was a later transfer actually the recovery event we were waiting for?

## External services

Somba talks to Nomba for payment actions and verification. It also talks to merchant endpoints through signed webhooks so the merchant’s own systems can react to billing changes.

Because external systems can be slow or inconsistent, Somba never assumes a single response is the whole truth. It keeps enough history to verify later.

## Architecture diagram

Architecture diagram will be placed here. It shows the full data flow from entry points (developers, customers, Nomba webhooks, and the scheduler) through the event queue, workers, state machine, and ledger, out to Nomba API and merchant endpoints.

![Architecture](./assets/architecture.png)
