"""Billing-period math: maps a plan interval to elapsed days.

Shared between subscription creation (api/subscriptions.py) and the charge
worker (workers/charge/worker.py, which advances the period after a
successful regular charge) so both compute period boundaries identically.
"""

from __future__ import annotations

from datetime import datetime, timedelta

INTERVAL_DAYS: dict[str, int] = {
    "day": 1,
    "week": 7,
    "month": 30,
    "year": 365,
}


def next_period_end(interval: str, interval_count: int, start: datetime) -> datetime:
    days = INTERVAL_DAYS.get(interval, 30) * interval_count
    return start + timedelta(days=days)
