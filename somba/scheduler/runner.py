"""APScheduler runner: periodic billing sweep (and reconciliation triggers)."""

from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from somba.db.session import SessionLocal
from somba.scheduler.billing_sweep import emit_due_billing_events

log = logging.getLogger(__name__)


def _billing_sweep_tick() -> None:
    """One scheduler tick: emit billing.due for everything due now."""
    db = SessionLocal()
    try:
        emit_due_billing_events(db)
    except Exception:  # noqa: BLE001
        # A failing tick must never kill the scheduler — log and wait for next.
        log.exception("billing sweep tick failed")
    finally:
        db.close()


def build_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        _billing_sweep_tick,
        trigger="interval",
        seconds=60,
        id="billing_sweep",
        max_instances=1,   # never run two sweeps at once
        coalesce=True,     # if ticks were missed, run once on resume, not N times
    )
    return scheduler


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    scheduler = build_scheduler()
    log.info("scheduler started")
    scheduler.start()  # blocks


if __name__ == "__main__":
    run()
