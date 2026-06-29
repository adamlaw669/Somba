# Overview

Somba is a managed recurring-billing platform for businesses that want to charge customers on a schedule without building billing logic themselves. It is designed for subscriptions, renewals, recovery, invoices, and customer self-service.

This page explains the product at a high level and who it is for.

## What Somba is

Somba is the billing layer that sits between a merchant and the payment rail. A company tells Somba what plan a customer is on, when the next bill should happen, and how to recover if a payment fails.

Somba then keeps track of the subscription lifecycle, creates invoices, schedules charging, handles retries, sends recovery prompts, and records what happened in a way the business can audit later.

## Who it is for

Somba is for teams that sell recurring services in Nigeria, including:

- SaaS tools that charge monthly or yearly
- Creator platforms with membership tiers
- Gym or wellness memberships
- Education platforms with ongoing access
- Businesses that need a reliable customer portal and billing history

It is not for a one-time checkout flow. If the product is a simple pay-now transaction, Somba is more machinery than needed.

## The one-liner

Somba is managed recurring billing for Nomba, with recovery logic that can retry at the right time, switch to transfer-based recovery when needed, and keep a clean record of every payment step.

## What problem it solves

The main problem is involuntary churn. A customer wants to stay, but the payment fails because the timing was bad or the rail behaved unexpectedly.

Somba tries to save that customer relationship by recovering the payment instead of treating every failure as a final loss.

## What makes it different

Most payment tools stop at "charge failed." Somba continues with the next useful step:

- Wait for a better funding window when the account is likely to recover
- Freeze the subscription when the result is unknown
- Reconcile late results instead of guessing
- Ask for a transfer when pulling money again is no longer sensible

That makes the product more than a billing tool. It becomes a recovery system.
