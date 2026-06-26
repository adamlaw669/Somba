# Getting Started

This page explains how to run Somba locally, which environment variables are required, and how to verify the sandbox with five day-one tests before touching production-like data.

## Local setup

This repository is currently a scaffold, so this page describes the intended local setup rather than a finished production installer.

The expected developer flow is:

1. Clone the repository.
2. Create a Python virtual environment.
3. Install the dependencies from `requirements.txt` or the future project package definition.
4. Copy `.env.example` to `.env` and fill in local values.
5. Start the API, scheduler, workers, and supporting services once implementation exists.

The idea is to keep the local environment close to production without making the setup hard to understand.

## Environment variables

The project expects the following environment variables:

- `PORT` - the HTTP port for the API
- `DATABASE_URL` - database connection string
- `REDPANDA_BROKERS` - queue broker address
- `NOMBA_BASE_URL` - base URL for Nomba requests
- `NOMBA_API_KEY` - API credential for Nomba
- `NOMBA_API_SECRET` - secret for Nomba-related auth
- `WEBHOOK_SIGNING_SECRET` - secret used to sign outbound webhooks

Other variables may be added later, but these are the core ones the scaffold already anticipates.

## Day-one sandbox tests

Before trusting the system with real billing, the first sandbox checks should prove the most important behaviors.

1. Create a merchant and confirm the API key is accepted.
2. Create a plan, customer, and subscription.
3. Trigger a due billing event and confirm it creates the expected invoice and charge attempt.
4. Simulate a timeout and confirm the subscription enters `payment_uncertain` instead of guessing.
5. Simulate a recovery event and confirm the subscription can heal back to `active`.

Those tests prove the core promises: charge once, recover safely, and reconcile truthfully.

## Common checks

- Confirm every record created for one merchant stays invisible to another merchant.
- Confirm idempotent retries do not create duplicate objects.
- Confirm outbound webhook signatures can be verified by the recipient.
- Confirm the ledger has both the intent and the final settlement for a completed charge.

## What this page is for

This page gives contributors a mental model for how the system should be brought up and verified. Once implementation is added, the exact commands can be filled in without changing the intent of the setup.
