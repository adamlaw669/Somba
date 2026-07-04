# SOMBA — THE FILM · Voiceover Script

**Runtime:** 3:26 · **Pace:** ~135 wpm — relaxed, confident, let the visuals breathe.
Read alongside the film; each block starts when the timecode hits. The scrub bar
has a tick mark at every scene start, and `→`/`←` skip 5 s if you drift.

> Delivery notes are in *italics*. Bold words deserve a small punch.

---

### 00:00 — COLD OPEN *(heartbeat pulse, wordmark rises)*

*(Wait for the pulse line to finish — speak as the letters rise, ~0:04)*

Every subscription business has a heartbeat.
It's the renewal. The charge that lands every month, quietly, on time.

This is **Somba** — Stripe Billing for Nomba, with a recovery engine
no global processor has.

---

### 00:14 — THE PROBLEM *(merchant cards, gears)*

A gym in Surulere. A school. A streaming service. An ISP.
Every one of them, rebuilding the **same billing engine** from scratch —
retry logic, dunning, ledger tracking. And most get the hard parts subtly wrong.

*(as the panel slides in, ~0:22)*

Then one night, a renewal fails. Silently. Nobody retries it.
Nobody calls. The customer is **gone — without ever deciding to leave.**

*(let the stamp slam, then:)* That's involuntary churn. And it compounds.

---

### 00:36 — THE MARKET *(yellow, counters, funnel)*

The stage this happens on is enormous.
Over **seven hundred billion dollars** moved through Nigeria's digital rails
in 2024 — one-point-oh-seven **quadrillion naira**, eleven **billion** instant
transactions.

Inside that: a hundred-and-fifty-billion-dollar recurring-billing segment —
subscriptions, utilities, insurance, content.
Somba's near-term target is just one percent of it.
And we know the demand is real — **sixty thousand businesses** already sell
subscriptions on Paystack alone. Proven. And still underserved.

---

### 00:54 — THE INSIGHT *(TIMING, NOT RETRYING)*

Here's the insight everything else is built on.

Most failed renewals in Nigeria aren't broken cards.
They're **empty accounts.** Retrying an empty account — on any rail —
just reaches the same empty account by a different road.

*(calendar lights up, ~1:02)*

So Somba doesn't retry harder. It retries **smarter** — rescheduling the charge
to when money is actually there. Like payday. *(ding)* Charge succeeded.

And when timing runs out, we don't keep pulling — we **switch direction**:
a transfer request to a dedicated virtual account. Nigeria runs on transfers.

*(pairs appear, ~1:08 — pick up tempo slightly)*

Five failure reasons. Five different answers.
Empty account? Reschedule. Dead card? Straight to transfer.
Soft decline? One retry. Timeout? Freeze and verify. Fraud signal? Full stop.

**Reason-aware recovery** — not blind retries.

---

### 01:18 — THE PRODUCT *(lifecycle rail)*

Under the hood, Somba is a multi-tenant billing engine.
Merchants integrate once, through one REST API.

Seven lifecycle states, one spine — watch the subscription move:
trialing… **active**… a payment slips: **past due**…
and here's the state almost nobody else has — **payment_uncertain.**

When Somba doesn't know what happened, it never guesses.
It **freezes, verifies, and confirms.**

*(orb travels back, ~1:34)*

And when recovery lands — the subscription **heals backward** to active.
No re-subscribe. No support ticket.

---

### 01:40 — TECHNICALLY STRONG *(zero double charges)*

Now, the part engineers will ask about: **zero double charges, by design.**

One — the ledger is written **before** we ever call Nomba.
A crash mid-charge loses nothing.
Two — a verify pass sweeps every five minutes; anything uncertain
resolves itself. No human in the loop.
Three — every charge attempt carries an **idempotency key**,
so a retried request can never charge twice.

*(stats land, ~1:51)*

Ninety-nine-nine uptime. Sub-sixty-second billing cycles.
Ten thousand charge attempts a minute. Three layers of protection.

---

### 02:02 — COMPETITION *(the table)*

So how does that compare?

Reason-aware recovery — **only Somba.**
Card-first with a transfer fallback — the gateways don't; Remita partly does.
A correctness ledger as the source of truth — **only Somba.**
Built for how Nigerians actually pay — the global platforms simply aren't.

*(typewriter line, ~2:15)*

The only **yes** in every row.

---

### 02:22 — BUSINESS MODEL *(money bag)*

And our incentives are pointed the right way:
**we only get paid when we save you money.**

A recovery success fee — charged only on revenue Somba actually rescues.
A tiered platform fee for plans, portal and dashboards.
And longer term, a revenue share with Nomba itself —
a billing layer **on** Nomba's rails, not a competitor to them.

---

### 02:38 — GYMFLOW *(phone demo)*

This isn't a slide-deck product. It's running, live.

GymFlow — a real gym frontend on the live Somba API.
A member signs up… gets charged… the payment **fails**…
Somba hands them a transfer account… and the membership
**restores itself** — automatically.

Every webhook you see streaming is real.
No admin console. No manual reconciliation.

---

### 03:00 — TEAM *(cards)*

We're four builders — **Team SetId.**
Sanni on frontend, Adam on data and AI, Quadri on software, Raufu on backend.

### 03:08 — THE ASK *(white)*

Three asks.
**One** — production API access and three-to-five pilot merchants,
to run Somba live for thirty days.
**Two** — placement in Nomba's developer ecosystem as a recommended billing layer.
**Three** — continued build support, to reach production grade in sixty days.

### 03:18 — CLOSE *(logo)*

*(slow down, land every word)*

Somba. One query answers **every naira.**
Built on Nomba rails.

*(hold for the end card — done.)*

---

## Rehearsal tips

- The music dips automatically at the Team section and fades on the close —
  those are your cue points if you get lost.
- Scene 4 (the insight) is the heart of the pitch. Slow down there.
- If a judge interrupts, hit **space** to pause — the film resumes exactly
  where it stopped, music and all.
- `F` = fullscreen, `M` = music toggle, `←`/`→` = ±5 seconds.
