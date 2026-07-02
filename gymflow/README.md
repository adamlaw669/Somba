# GymFlow

The gym-membership demo app for **Somba** — managed recurring billing & recovery.

GymFlow shows what a real business sitting on top of Somba looks like to its
members. It walks the full subscription lifecycle end to end: a member signs up,
gets billed, a payment fails, recovery kicks in (timing retry or a transfer
fallback to a dedicated account), and the membership heals itself back to active
— with every webhook event streaming live.

## Stack

- Next.js 16 (App Router) + React 19 + TypeScript
- Tailwind CSS v4
- Zustand store that talks to the live Somba API (or a built-in local mock)

## Live vs. local mode

GymFlow runs against the **live Somba API** when `SOMBA_API_KEY` is set, and
falls back to a **local mock** otherwise — the header shows which one is active.

- Copy `.env.example` to `.env.local` and set `SOMBA_API_KEY` (create a merchant
  via `POST /v1/merchants` on your Somba instance to get one — it's shown once).
- The browser never sees the key: it calls our own `/api/somba/*` route handlers
  (`app/api/somba/`), which proxy to Somba using the server-side key and add the
  `Authorization` + `Idempotency-Key` headers.
- **Live** covers everything the API exposes: plans, sign-up (create customer +
  subscription), status, invoices, the real webhook/outbox event feed, and
  plan changes with real proration returned by Somba.
- The API doesn't expose pause/resume/cancel/retry/transfer/verify triggers yet
  (those run server-side off the scheduler + Nomba webhooks), so those recovery
  transitions in the demo cockpit are simulated locally and clearly labelled.

## Screens

| Route | What it is |
|---|---|
| `/` | Landing — gym branding, plan selection |
| `/join` | Sign-up — name, email, card tokenisation |
| `/membership` | Membership status — state badge, next bill date, plan, lifecycle rail, manage actions + **demo cockpit** |
| `/membership/billing` | Payment history — invoices with status chips + charge-attempt ledger |
| `/membership/recovery` | Recovery — plain-English failure reason + transfer-fallback account number |
| `/membership/card` | Billing portal — update card, retry payment |
| `/events` | Webhook event viewer — live signed-event feed with payload inspector |

## Run it

```bash
npm install
npm run dev      # http://localhost:3000
```

Production build:

```bash
npm run build && npm start
```

## Demo flow

1. Pick a plan on the landing page and join.
2. On the membership page, use the **demo cockpit** to drive scenarios:
   renew, fail on an empty account, hard-decline into a transfer fallback, or a
   charge timeout that freezes into `payment_uncertain`.
3. Heal it — retry, send the transfer, or run the verify pass — and watch the
   pass flip back to active.
4. Open **Events** to see every webhook Somba fired, with signatures and payloads.

## Design

Yellow / black / white, athletic-industrial. Display type is Archivo, body is
Hanken Grotesk, and data (account numbers, idempotency keys, payloads) is set in
JetBrains Mono. Brand imagery is high-contrast monochrome with a single electric
yellow accent. No real money moves — every charge is simulated.

Built by Quadri for the Nomba × DevCareer 2026 hackathon.
