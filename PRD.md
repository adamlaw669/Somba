# Somba Product Requirements Document

## 1. What is Somba

Somba is a recurring-billing platform for Nigerian businesses that want to charge customers on a schedule without building the billing machinery themselves. A merchant connects once through an API, and Somba handles plans, subscriptions, invoices, retries, recovery, and customer notifications in the background.

Think of it as Stripe Billing adapted for Nomba and for the realities of Nigerian payment behavior.

## 2. The problem

Recurring payments are easy when money always lands on time. In practice, many subscriptions fail because a customer’s account is empty for a few hours, a card times out, or a webhook arrives late.

That creates involuntary churn. The customer did not choose to leave, but the business still loses revenue because nobody follows up well enough or safely enough.

## 3. The insight

Somba does not treat every failure the same way. It first asks why the payment failed, then chooses the least harmful recovery path.

For empty-account failures, the best move is often to wait for a better funding window instead of immediately trying again. If retrying no longer makes sense, Somba stops pulling and asks the customer to push money to a dedicated virtual account, which fits how payments often clear in Nigeria.

## 4. How it works

Somba follows a simple chain:

1. A bill becomes due.
2. Somba writes down the intent to charge before it calls Nomba.
3. Nomba is asked to charge the customer.
4. If the result is clear, the subscription moves forward or into recovery.
5. If the result is unclear, Somba freezes the subscription and verifies the result later.
6. If retries fail, Somba falls back to transfer-based recovery.
7. Every important event is recorded so the system can prove what happened later.

All money values are stored in kobo, the smallest unit of naira, like cents to dollars.

## 5. The subscription lifecycle

Somba uses seven states. These states describe where the subscription is in its life.

| State | Plain English meaning |
|---|---|
| trialing | The customer is using the product for free for a limited time. |
| active | The subscription is paid and current. |
| past_due | A payment failed, but the customer still has a chance to recover. |
| payment_uncertain | The payment result is not yet known, so the subscription is frozen. |
| paused | Billing is temporarily stopped. |
| cancelled | The subscription was ended by the customer or merchant. |
| expired | The subscription ended naturally and will not continue. |

A simple example: a gym membership in Lagos.

The member starts in `trialing` during a free trial. When the first charge succeeds, the plan becomes `active`. If the card fails because the account is empty, the member becomes `past_due`, which is like a grace period. If the payment gateway times out, the membership becomes `payment_uncertain`, which means Somba must verify before doing anything else. If the member pauses the plan while traveling, the subscription becomes `paused`. If they cancel, it becomes `cancelled`. If the trial ends with no paid plan, it becomes `expired`.

The two key heal-backward paths are:

| From | To | Meaning |
|---|---|---|
| past_due | active | A late retry or a pushed transfer saved the subscription. |
| payment_uncertain | active | Verification confirmed the payment really succeeded. |

## 6. The recovery engine

Somba does not use blind retrying. It looks at the reason for the failure.

If the account looks empty, Somba tries again at a better time, such as near payday or after signs that money has entered the account. If the card has a soft decline, Somba gives one retry before moving to transfer fallback. If the card is dead or the failure is clearly risky, Somba stops pulling and asks for a push transfer instead.

This matters because retrying the same pull at the wrong time usually fails again. In Nigeria, the better recovery path is often to ask the customer to push funds into a dedicated virtual account.

## 7. Reconciliation and the ledger

Somba keeps a ledger so it can prove what it intended to charge and what Nomba actually confirmed. The ledger is not just an accounting view. It is how Somba avoids double charges, lost charges, and confusion after timeouts.

The process is:

1. Somba writes a `ledger_intent` before calling Nomba.
2. If the result comes back clearly, Somba writes a matching settlement record.
3. If the result is missing or delayed, the subscription moves to `payment_uncertain`.
4. A verify pass asks Nomba for the true result using the order reference.
5. A periodic sweep catches anything that still needs attention.
6. Transfer recovery uses the same matching logic when a customer pushes money into a dedicated account.

This is the main correctness moat. It lets Somba heal late payments and also explain every naira that moved.

## 8. Proration

Proration is how Somba handles a plan change in the middle of a billing period.

If a customer upgrades, Somba charges only the extra amount for the remaining days. If a customer downgrades, Somba credits the unused value into `credit_balance` and applies that balance to the next renewal.

The first calculation is done in kobo, not naira floats.

| Case | Result |
|---|---|
| Upgrade | Charge the difference immediately. |
| Downgrade | Store the credit and reduce the next bill. |
| Full credit coverage | Skip the next Nomba charge entirely. |

Example: a creator platform customer switches from a small plan to a larger plan halfway through the month. Somba bills only the remaining uplift instead of charging the full new plan again.

## 9. Multi-tenancy and customer portal

Somba is multi-tenant, which means many merchants can use one deployment without seeing each other’s data. Every record includes `merchant_id`, and every application query is filtered by merchant.

If a merchant guesses another merchant’s subscription ID, Somba returns a not-found response instead of exposing the record.

The customer portal lets a subscriber update payment details, view invoices, see recovery status, and manage their subscription without contacting support.

## 10. Non-functional requirements

### Correctness

Somba must be strict about money movement because a mistake can create double charges, lost charges, or false recovery. The system uses multiple safeguards so the same payment cannot be applied twice and every charge attempt ends in a known state.

Targets:

- Zero double charges.
- Zero silent lost charges.
- No illegal state transitions.
- Every intent reaches a terminal status.

### Durability

Billing cannot depend on a single process staying alive. Somba records intent before action, uses an outbox so important events are not lost, and keeps its ledger append-only so history cannot be rewritten casually.

Targets:

- Outbox guarantee: once an event is stored, it is eventually published.
- RPO = 0 on the charge path.
- Reconciliation must survive process crashes.

### Availability

Billing should keep working even when workers restart or a scheduled job is delayed. The system is allowed to recover later, but not to lose work.

Targets:

- API server: 99.9% uptime.
- Workers: graceful degradation.
- RTO: 2 minutes for workers, 30 seconds for the API server.

### Latency

Fast responses matter because merchants need quick confirmations and customers should not wait long for state changes. Billing itself can be asynchronous, but the API must stay responsive.

Targets:

- GET requests: p95 under 100 ms.
- POST and PATCH requests: p95 under 300 ms.
- Billing cycle end-to-end: p95 under 60 seconds.
- First webhook attempt within 30 seconds.
- `payment_uncertain` verified within 5 minutes.

### Throughput

The system must survive billing spikes, such as a large batch of renewals on the same day. The queue absorbs bursts while workers drain them at a steady pace.

Targets:

- 10,000 charge attempts per minute at peak.
- Scheduler queries must use the `(merchant_id, status, next_bill_date)` index.
- No full table scan for the main billing sweep.

### Security

Billing and payment data must stay protected because leaks are expensive and hard to recover from. Keys are shown once, webhooks are signed, and inbound events are checked before any state changes happen.

Targets:

- API keys hashed at rest with bcrypt.
- Nomba inbound webhooks verified with HMAC-SHA256 before processing.
- Outbound webhooks signed per merchant.
- Token keys never appear in logs or error messages.
- Tenant isolation enforced through `merchant_id` in every query.

### Observability

Somba needs to explain where money is stuck, where recovery is working, and when a queue is falling behind. Good metrics are part of the product because billing problems are operational problems.

Targets:

- Alert if any intent is pending for more than 10 minutes.
- Alert if `payment_uncertain` does not decrease for 15 minutes.
- Alert if queue depth grows for 5 consecutive minutes.
- Alert immediately on any double-charge signal.

## 11. What is out of scope

Somba is not trying to solve every billing problem on day one.

- Direct-debit mandate management is out of scope.
- Multi-currency support is out of scope.
- Tax invoicing is out of scope.
- Card network dispute handling is out of scope.
- Payroll or wallet features are out of scope.
- Manual finance reconciliation tools beyond the billing ledger are out of scope.

## 12. Architecture overview

![Architecture](./docs/assets/architecture.png)

Image to be added - shows full system flow from entry points through event queue to external services.

The diagram includes:

- Developers and merchants entering through the API.
- Nomba inbound webhooks entering through the webhook intake path.
- A scheduler that finds due billing work.
- An outbox that stores events before they are published.
- Relay shards labeled `S0` to `S3` that move events into queue partitions.
- Event queues that feed the workers.
- A state machine that controls legal subscription transitions.
- A ledger that records intent and settlement.
- Recovery and reconciliation workers that repair uncertain or failed charges.
- The outbound webhook endpoint that notifies merchants.

## 13. Project structure

The codebase is intentionally small and modular.

- [`./`](./) - repository root
  - [`./docs/`](./docs/) - product and engineering documentation
    - [`./docs/assets/`](./docs/assets/) - architecture images and other static assets
  - [`./somba/`](./somba/) - Python package for the application
    - [`./somba/api/`](./somba/api/) - REST API route modules
      - [`./somba/api/middleware/`](./somba/api/middleware/) - API middleware helpers
    - [`./somba/scheduler/`](./somba/scheduler/) - scheduled billing and reconciliation triggers
    - [`./somba/workers/`](./somba/workers/) - asynchronous workers
      - [`./somba/workers/charge/`](./somba/workers/charge/) - charge worker
      - [`./somba/workers/recovery/`](./somba/workers/recovery/) - recovery engine and classifier
      - [`./somba/workers/reconcile/`](./somba/workers/reconcile/) - verification and sweep workers
    - [`./somba/nomba/`](./somba/nomba/) - Nomba client and inbound intake
    - [`./somba/db/`](./somba/db/) - database models, session, and migrations
      - [`./somba/db/migrations/`](./somba/db/migrations/) - Alembic migration environment
  - [`./tests/`](./tests/) - unit and integration tests
    - [`./tests/unit/`](./tests/unit/) - unit tests
    - [`./tests/integration/`](./tests/integration/) - integration tests
  - [`./scripts/`](./scripts/) - developer scripts and demo seed helpers

## 14. Links to all docs pages

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
