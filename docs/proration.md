# Proration

This page explains how Somba calculates mid-cycle upgrades and downgrades, how it stores proration credits, and how those credits affect the next renewal.

## The formula

Proration is a fair way to split a billing period when the customer changes plans halfway through.

The idea is:

`credit = (old plan amount / days in period) × days remaining`

`charge = (new plan amount / days in period) × days remaining`

`net = charge - credit`

All of this is calculated in kobo, not floating-point naira values.

## Upgrade flow

When a customer upgrades:

1. Somba calculates how much value is left in the old plan.
2. Somba calculates the cost of the new plan for the remaining days.
3. Somba charges the difference immediately if the result is positive.

Example: a business moves from a small creator tier to a larger one halfway through the month. Somba does not charge the full new month again; it only charges the extra value for the days left.

## Downgrade flow

When a customer downgrades:

1. Somba calculates the unused value from the old plan.
2. Somba stores that value as a credit.
3. The next renewal checks the credit before charging.

If the credit covers the full renewal, Somba does not call Nomba for that cycle. The stored credit already covers the cost.

## Credit balance

`credit_balance` is the amount of future billing value that the customer has already earned.

It is useful for:

- Downgrade adjustments
- Goodwill credits
- Partial month changes
- Reducing friction when the next renewal is due

Credits should be treated like money already reserved for the customer, not like a discount code that can disappear without explanation.

## Why this matters

Proration is one of the easiest ways to overcharge or undercharge if it is handled casually. Somba keeps it explicit so customers are treated fairly and merchants can explain the bill.
