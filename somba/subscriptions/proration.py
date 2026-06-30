"""Proration calculator: credit, charge, and net — all in kobo.

Formula (from the PRD):
  credit = round(old_amount * remaining_days / total_days)
  charge = round(new_amount * remaining_days / total_days)
  net    = charge - credit

Positive net  → upgrade: caller creates an immediate proration invoice.
Zero or neg   → downgrade: caller stores abs(net) in customer.credit_balance.

All arithmetic is done on integers (kobo) to avoid floating-point drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProrationResult:
    credit_kobo: int    # value of unused old-plan days
    charge_kobo: int    # cost of new plan for remaining days
    net_kobo: int       # charge - credit  (positive → customer owes more)
    remaining_days: int
    total_days: int


def _strip_tz(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


def calculate(
    *,
    old_plan_amount: int,
    new_plan_amount: int,
    period_start: datetime,
    period_end: datetime,
    change_date: datetime,
) -> ProrationResult:
    """Return the proration breakdown for a mid-cycle plan change.

    All amounts in kobo.  Normalises timezone-aware and naive datetimes so
    SQLite-stored (naive) and Python (aware) values can be compared safely.
    """
    start = _strip_tz(period_start)
    end = _strip_tz(period_end)
    change = _strip_tz(change_date)

    total_seconds = max((end - start).total_seconds(), 1)
    remaining_seconds = max((end - change).total_seconds(), 0)

    # Work in integer days (round down for remaining, round from total)
    total_days = max(int(total_seconds / 86400), 1)
    remaining_days = int(remaining_seconds / 86400)

    credit_kobo = _prorate(old_plan_amount, remaining_days, total_days)
    charge_kobo = _prorate(new_plan_amount, remaining_days, total_days)
    net_kobo = charge_kobo - credit_kobo

    return ProrationResult(
        credit_kobo=credit_kobo,
        charge_kobo=charge_kobo,
        net_kobo=net_kobo,
        remaining_days=remaining_days,
        total_days=total_days,
    )


def _prorate(amount: int, remaining: int, total: int) -> int:
    """Integer proration: round(amount * remaining / total)."""
    return round(amount * remaining / total)
