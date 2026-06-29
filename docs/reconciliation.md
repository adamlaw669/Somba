# Reconciliation

This page explains how Somba matches ledger intents to ledger settlements and how it uses the verify pass and periodic sweep to resolve uncertain payments. It also explains how transfer fallback recovery uses the same matching engine.

## Ledger intents

A ledger intent is Somba's written promise that it meant to collect a payment.

It is stored before the payment call happens, which means the system keeps proof even if the process crashes after making the request.

Typical fields include:

- Who the customer is
- Which subscription and invoice the charge belongs to
- The amount in kobo
- The idempotency key used for the attempt
- The order reference used to speak to Nomba later

## Ledger settlements

A ledger settlement is the confirmation that money actually moved or that the system has a definitive result.

Settlements can come from:

- A webhook from Nomba
- A verification call after a timeout
- A sweep job that checks for missing outcomes
- A transfer push that matches an open invoice

## Verify pass

The verify pass is what Somba uses when a charge result is unknown.

Rather than guess, Somba asks Nomba for the final answer using the order reference. That tells the system whether the charge succeeded, failed, or needs another action.

This protects against a very common failure mode: the customer was charged, but the server never saw the confirmation in time.

## Periodic sweep

The periodic sweep is the cleanup job that keeps the ledger honest.

It scans for things that should not remain unresolved for too long:

- Intents that have no matching settlement
- Subscriptions stuck in `payment_uncertain`
- Old charge attempts that need another look
- Events that should have been published but were not yet

The sweep is what keeps rare edge cases from becoming permanent messes.

## Transfer recovery matching

Transfer recovery uses the same matching idea as card settlement.

When a customer pushes money into a dedicated virtual account, Somba looks for a transfer that can be matched to an open invoice. If the match is good, the system marks the recovery as complete and heals the subscription backward.

This is important because the same engine that catches failures is also what proves the recovery succeeded.

## What can be matched

Somba can compare:

- Order reference
- Amount
- Invoice status
- Open subscription state
- Transfer reference

If the details line up, the payment is treated as recovered. If they do not, Somba flags the record for review instead of pretending everything is fine.
