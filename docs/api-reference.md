# API Reference

This page lists the public API endpoints, the authentication rules, the idempotency header, the standard error shape, and the outbound webhook events merchants can subscribe to.

## Authentication

The API uses bearer tokens.

Example:

`Authorization: Bearer sk-somba-<key_id>.<secret>`

The token identifies the merchant and is the first gate for access control. The `key_id` helps Somba look up the correct merchant, and the secret part is checked against the stored bcrypt hash. If a request does not present a valid token, it is rejected.

## Idempotency

Mutating endpoints require an `Idempotency-Key` header.

This means if a client retries the same request because of a timeout or network problem, Somba can recognize that it has already seen the request and should not create a second subscription, second invoice, or second charge attempt.

In plain English: doing the same action twice should have the same effect as doing it once.

Somba stores these request fingerprints in an internal idempotency record so retries can be handled safely across process restarts.

## Error shape

All errors use the same structure:

```json
{
  "error": {
    "code": "machine_readable_code",
    "message": "Human readable explanation",
    "param": "optional_field_name"
  }
}
```

This makes errors easy for both developers and support teams to understand.

## Plans

| Method | Path | What it does |
|---|---|---|
| POST | `/v1/plans` | Create a plan. |
| GET | `/v1/plans` | List plans. |
| GET | `/v1/plans/:id` | Read one plan. |
| PATCH | `/v1/plans/:id` | Update a plan. |
| DELETE | `/v1/plans/:id` | Archive or remove a plan. |

## Customers

| Method | Path | What it does |
|---|---|---|
| POST | `/v1/customers` | Create a customer record. |
| GET | `/v1/customers/:id` | Read a customer. |
| PATCH | `/v1/customers/:id` | Update customer details. |

## Subscriptions

| Method | Path | What it does |
|---|---|---|
| POST | `/v1/subscriptions` | Start a subscription. |
| GET | `/v1/subscriptions/:id` | Read a subscription. |
| POST | `/v1/subscriptions/:id/cancel` | Cancel a subscription. |
| POST | `/v1/subscriptions/:id/pause` | Pause a subscription. |
| POST | `/v1/subscriptions/:id/resume` | Resume a paused subscription. |
| POST | `/v1/subscriptions/:id/retry` | Ask Somba to retry a failed payment. |
| PATCH | `/v1/subscriptions/:id` | Change the plan and calculate proration. |

## Invoices

| Method | Path | What it does |
|---|---|---|
| GET | `/v1/invoices` | List invoices. |
| GET | `/v1/invoices/:id` | Read one invoice. |

## Webhooks

| Method | Path | What it does |
|---|---|---|
| POST | `/v1/webhooks/nomba` | Receive Nomba events after HMAC verification. |

Inbound webhooks are verified before any state change happens.

## Events replay

| Method | Path | What it does |
|---|---|---|
| GET | `/v1/events` | List published events. |
| POST | `/v1/events/:id/replay` | Replay a prior event intentionally. |

## Outbound webhook events

Somba can notify a merchant when important things happen.

Typical outbound events include:

- `invoice.created`
- `charge.succeeded`
- `charge.failed`
- `charge.retrying`
- `charge.recovered`
- `transfer.requested`
- `transfer.reconciled`
- `subscription.past_due`
- `subscription.paused`
- `subscription.cancelled`
- `payment.uncertain`
- `payment.resolved`
- `anomaly.detected`

Outbound webhooks are signed per merchant so the receiving system can trust the source.
