# Non-Functional Requirements

This page collects the correctness, durability, availability, latency, throughput, security, and observability targets that keep billing safe and predictable.

## Correctness

Billing systems must be correct before they are clever. If money moves the wrong way, the business loses trust very quickly.

Targets:

- Zero double charges
- Zero silent lost charges
- No illegal state transitions
- Every charge intent must reach a terminal status

Enforcement:

- Unique billing locks
- Unique idempotency keys
- Deterministic order references
- Exhaustive state transition rules

## Durability

Billing work cannot disappear if a worker crashes or a network call times out.

Targets:

- Outbox guarantee: once an event is stored, it will be published
- RPO = 0 on the charge path
- The ledger is append-only

Enforcement:

- Intent written before action
- Reconciliation after uncertainty
- Retryable relay publishing

## Availability

Customers and merchants expect billing to keep moving even when the system is under stress.

Targets:

- API server: 99.9% uptime
- Workers: graceful degradation
- RTO: 2 minutes for workers
- RTO: 30 seconds for the API server

Enforcement:

- Stateless API design
- Queue buffering during worker downtime
- Missed scheduler ticks catch up later instead of losing work

## Latency

Fast responses matter because merchants and customers need quick confirmation.

Targets:

- GET requests: p95 under 100 ms
- POST and PATCH requests: p95 under 300 ms
- End-to-end billing cycle: p95 under 60 seconds
- First webhook attempt within 30 seconds
- `payment_uncertain` verified within 5 minutes

Enforcement:

- Lightweight read paths
- Queue-based async work
- Fast verification on uncertain charges

## Throughput

Billing spikes happen. Many subscriptions may renew at once, and the system must absorb that burst without falling over.

Targets:

- 10,000 charge attempts per minute
- Scheduler must use the `(merchant_id, status, next_bill_date)` index
- No full table scan for the main sweep

Enforcement:

- Queue partitions
- Ordered processing per subscription
- Database indexes designed for the main query path

## Security

Billing data and payment tokens must stay protected because the cost of mistakes is high.

Targets:

- API keys hashed at rest with bcrypt
- Nomba inbound webhooks verified with HMAC-SHA256 before state changes
- Outbound webhooks signed per merchant
- Token keys never logged
- Tenant isolation enforced at the database query level

Enforcement:

- Signed requests
- Explicit merchant scoping
- Sensitive data kept out of logs and errors

## Observability

If something goes wrong, the team needs to know whether it is a product issue, a payment issue, or a queue issue.

Targets:

- Alert if any intent is pending for more than 10 minutes
- Alert if `payment_uncertain` does not decrease for 15 minutes
- Alert if queue depth grows for 5 consecutive minutes
- Alert immediately on any double-charge signal

Enforcement:

- Metrics for billing lag, queue depth, recovery rate, and orphan settlements
- Alerts tied to the business risks that matter
