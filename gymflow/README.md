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
- Zustand for the in-memory store that mocks the Somba API

The mock API (`lib/store.ts`) mirrors Somba's data model and event shapes, so it
can be swapped for the live API later by changing only the data source — not the
screens.

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
