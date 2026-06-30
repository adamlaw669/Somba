"""APScheduler runner: periodic billing sweep (and reconciliation triggers)."""

from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from somba.db.session import SessionLocal
from somba.scheduler.billing_sweep import emit_due_billing_events
from somba.observability.alerts import check_pending_intents, PaymentUncertainMonitor


log = logging.getLogger(__name__)

# One long-lived monitor — it tracks the payment_uncertain count across ticks.
_payment_uncertain_monitor = PaymentUncertainMonitor()

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

def _pending_intents_tick() -> None:
    """Alert on ledger intents stuck pending past the threshold."""
    db = SessionLocal()
    try:
        check_pending_intents(db)
    except Exception:  # noqa: BLE001
        log.exception("pending-intent alert tick failed")
    finally:
        db.close()


def _payment_uncertain_tick() -> None:
    """Alert if the payment_uncertain count is stuck (recon worker down)."""
    db = SessionLocal()
    try:
        _payment_uncertain_monitor.check(db)
    except Exception:  # noqa: BLE001
        log.exception("payment_uncertain monitor tick failed")
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
    scheduler.add_job(
        _pending_intents_tick,
        trigger="interval",
        minutes=1,
        id="pending_intent_alert",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        _payment_uncertain_tick,
        trigger="interval",
        minutes=5,
        id="payment_uncertain_alert",
        max_instances=1,
        coalesce=True,
    )
    
    return scheduler


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    scheduler = build_scheduler()
    log.info("scheduler started")
    scheduler.start()  # blocks


if __name__ == "__main__":
    run()
