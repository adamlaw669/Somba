# Recovery Engine

This page explains how Somba decides what to do after a payment failure. It covers reason classes, timing-based retries, and the transfer fallback path that asks the customer to push money to a dedicated account.

## Failure reasons

Somba does not use one generic failure message. It groups failures into classes so the next step is sensible.

| Failure class | What it usually means | Somba's response |
|---|---|---|
| empty_account | The account probably had no money at that moment. | Try again later when funds are more likely to be present. |
| broken_card | The card is no longer useful, expired, or hard declined. | Stop pulling and move to transfer fallback. |
| transient | A temporary issue happened, such as a soft decline. | Retry once, then decide whether to switch paths. |
| risk | The payment looked unsafe or was blocked for fraud reasons. | Stop and do not keep pushing. |
| unknown | The reason is unclear. | Use a bounded recovery path and then fall back safely. |

## Timing-based recovery

Timing-based recovery means trying again when the customer is more likely to have money in the account.

Somba can use signals like:

- Expected payday
- Morning-after funding patterns
- A recent incoming transfer
- A merchant-defined retry window

The point is simple: if a customer was empty at 8:00 a.m., that is not proof they will still be empty later in the day. Somba tries to recover at a more reasonable time instead of creating a noisy series of failed charges.

## Transfer fallback

When pull-based retries stop making sense, Somba switches to transfer fallback.

Instead of continuing to pull from the same card or account, Somba asks the customer to push money into a dedicated virtual account. That works better for many Nigerian payment behaviors because transfers are familiar, visible, and easier to reconcile after the fact.

This is not a "failure and give up" path. It is a different recovery path that still protects the subscription.

## Why not a second pull rail

Using a second pull rail sounds helpful, but it often does not solve the real problem.

If the first failure happened because the account was empty, the second pull rail often reaches the same empty account through a different route. That just creates more noise, more failed attempts, and more risk of annoying the customer.

Somba’s judgment is that timing plus transfer fallback is more honest and more effective than blind rerouting between pull rails.

## Recovery examples

### Empty account

The customer’s card looked valid, but the balance was not there. Somba waits and retries later, ideally when money is more likely to arrive.

### Soft decline

The payment was probably fine, but the bank said "try again later." Somba gives one retry and then chooses the safer path.

### Hard decline

The card is effectively dead. Somba stops trying to pull and asks for a transfer instead.

### Unknown reason

When the failure is unclear, Somba avoids extreme behavior. It keeps the recovery path bounded so the system remains safe and predictable.
