# Data Model

This page documents the 14 tables used by Somba, the key columns in each table, and the indexes that keep billing and reconciliation fast.

All money values are stored in kobo, the smallest unit of naira, like cents to dollars.

## Merchants

Stores each business using Somba.

- Key fields: `id`, `name`, `api_key_hash`, `webhook_url`, `webhook_secret`
- Why it matters: every other record belongs to one merchant

## Plans

Stores the billing plans a merchant offers.

- Key fields: `id`, `merchant_id`, `name`, `amount`, `currency`, `interval`, `interval_count`, `trial_days`, `status`
- Why it matters: subscriptions point to plans, and the plan defines the amount and cadence

## Customers

Stores the customer identity within a merchant account.

- Key fields: `id`, `merchant_id`, `external_id`, `email`, `name`, `token_key`, `va_id`, `va_account_no`, `credit_balance`
- Why it matters: this is where customer identity, payment token, and transfer credit live

## Subscriptions

Stores the live billing relationship between a customer and a plan.

- Key fields: `id`, `merchant_id`, `customer_id`, `plan_id`, `status`, `current_period_start`, `current_period_end`, `next_bill_date`, `trial_end`, `cancel_at_period_end`, `cancelled_at`, `paused_at`
- Key index: `(merchant_id, status, next_bill_date)`
- Why it matters: this is the main table the scheduler reads to find what needs billing

## Invoices

Stores the bill for a billing period.

- Key fields: `id`, `merchant_id`, `subscription_id`, `customer_id`, `amount`, `status`, `type`, `period_start`, `period_end`, `due_date`, `paid_at`
- Key constraint: unique on `(subscription_id, period_start)`
- Why it matters: invoices are the financial record of what was owed

## Invoice line items

Stores the breakdown of an invoice.

- Key fields: `id`, `invoice_id`, `merchant_id`, `type`, `description`, `amount`, `period_start`, `period_end`
- Why it matters: this explains where the amount came from, including proration credits and charges

## Charge attempts

Stores each attempt to collect money.

- Key fields: `id`, `merchant_id`, `subscription_id`, `invoice_id`, `idempotency_key`, `order_reference`, `amount`, `status`, `failure_reason`, `failure_class`, `attempt_number`
- Key constraints: unique `idempotency_key`, unique `order_reference`
- Why it matters: this is the record of each try, successful or not

## Billing locks

Stores a safety lock so the same subscription period is not billed twice.

- Key fields: `id`, `subscription_id`, `billing_period`, `status`
- Key constraint: unique on the subscription-period pair
- Why it matters: it is one of the protections against double charging

## Outbox events

Stores events before they are published.

- Key fields: `id`, `merchant_id`, `aggregate_type`, `aggregate_id`, `event_type`, `payload`, `partition_key`, `status`
- Key index: `(status, id)` where status is pending
- Why it matters: if the process crashes, the event still exists and can be published later

## Ledger intents

Stores the written intent to collect money.

- Key fields: `id`, `merchant_id`, `subscription_id`, `invoice_id`, `charge_attempt_id`, `idempotency_key`, `order_reference`, `amount`, `status`
- Why it matters: it proves the system meant to charge before it called Nomba

## Ledger settlements

Stores the confirmed result of a payment or transfer.

- Key fields: `id`, `merchant_id`, `intent_id`, `invoice_id`, `order_reference`, `transaction_ref`, `amount`, `source`, `status`, `raw_payload`
- Key indexes: `order_reference`, `transaction_ref`
- Why it matters: this is the proof that money actually moved

## Subscription events

Stores the history of state changes.

- Key fields: `id`, `subscription_id`, `merchant_id`, `from_status`, `to_status`, `trigger`, `metadata`
- Why it matters: this is the audit trail for how the subscription changed over time

## Recovery schedules

Stores future recovery attempts.

- Key fields: `id`, `merchant_id`, `subscription_id`, `invoice_id`, `charge_attempt_id`, `scheduled_for`, `reason_class`, `attempt_number`, `status`
- Key index: `(status, scheduled_for)` where status is scheduled
- Why it matters: timing-based recovery needs a queue of future actions

## Webhook deliveries

Stores outbound webhook attempts to merchants.

- Key fields: `id`, `merchant_id`, `event_type`, `payload`, `signature`, `status`, `attempt_count`, `next_retry_at`
- Why it matters: merchants must not miss important billing events just because one delivery failed

## Why the model is structured this way

The model separates "what we meant to do," "what we tried," and "what actually happened." That separation makes recovery and auditability much safer.
