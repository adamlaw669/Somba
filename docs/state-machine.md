# State Machine

This page explains the seven subscription states, the legal transitions between them, and why `payment_uncertain` is treated differently from normal failed payments.

## The seven states

| State | Plain English meaning | Customer experience |
|---|---|---|
| trialing | The subscription is active for free during a trial period. | The customer can use the product, but billing has not started yet. |
| active | The subscription is paid and current. | Everything works normally. |
| past_due | A payment failed, but the subscription is still being recovered. | The customer may still have access during grace handling. |
| payment_uncertain | The result of a payment is not known yet. | The subscription is frozen until Somba verifies the truth. |
| paused | Billing is intentionally stopped for now. | The customer is temporarily parked, not lost. |
| cancelled | The subscription ended by choice. | No further billing should happen unless a new subscription is created. |
| expired | The subscription ended naturally, such as after a trial or term. | The plan has run its course. |

## Transition table

| Current state | Event | Next state | Why |
|---|---|---|---|
| trialing | first successful charge | active | The trial converted into a paying subscription. |
| trialing | trial ends with no payment | expired | The trial finished and nothing renewed. |
| active | charge fails with recoverable reason | past_due | Somba gets a chance to recover the payment. |
| active | charge times out | payment_uncertain | The system cannot guess, so it freezes. |
| active | pause request | paused | The merchant or customer asked for a temporary stop. |
| active | cancel request | cancelled | The subscription was deliberately ended. |
| past_due | retry succeeds | active | The subscription has been healed. |
| past_due | transfer arrives and matches open invoice | active | The customer recovered by pushing money in. |
| payment_uncertain | verify confirms success | active | The missing result was actually successful. |
| payment_uncertain | verify confirms failure | past_due | The system now knows it needs recovery. |
| paused | resume request | active | Billing starts again. |
| cancelled | recreate new plan | trialing or active | A new subscription must be created deliberately. |
| expired | recreate new plan | trialing or active | A new subscription starts fresh. |

Any transition not listed above is rejected. That is deliberate. It prevents accidental state changes that could create double billing or phantom access.

## Heal-backward

Heal-backward means moving from a worse billing state back to a healthy one.

The important heal-backward paths are:

- `past_due → active`
- `payment_uncertain → active`

This is important because a late success should still count. If the payment arrives after the first attempt looked failed, Somba should still be able to heal the subscription instead of leaving the customer stuck in a penalty state.

## `payment_uncertain`

This state exists for one reason: a timeout is not the same thing as a failure.

If Nomba has not confirmed the outcome yet, Somba does not know whether the money moved. Rather than risk a double charge, the subscription is frozen in `payment_uncertain` and a verification step is used to settle the truth later.

That behavior protects both sides:

- The merchant does not lose a successful payment
- The customer does not get charged twice
- The system does not guess

## Example in plain English

Imagine a gym membership.

- The customer signs up and gets `trialing`
- The first payment succeeds and the membership becomes `active`
- A later renewal fails because the account is empty, so the membership becomes `past_due`
- Somba retries at a better time and the membership returns to `active`
- Another renewal times out, so the membership becomes `payment_uncertain`
- A verification pass later confirms the payment did go through, so the membership returns to `active`

That is the basic lifecycle Somba is designed to protect.
