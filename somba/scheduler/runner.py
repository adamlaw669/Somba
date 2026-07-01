"""APScheduler runner: periodic billing sweep (and reconciliation triggers)."""

from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from somba.db.session import SessionLocal
from somba.scheduler.reconciliation_triggers import reconcile_sweep_tick, verify_pass_tick
from somba.observability.alerts import check_pending_intents, PaymentUncertainMonitor
from somba.observability.queue_depth import check_queue_depth
from somba.queue.config import BILLING_CONSUMER_GROUP
from somba.workers.charge import worker as charge_worker
from somba.workers.emitter import emitter


log = logging.getLogger(__name__)

# One long-lived monitor — it tracks the payment_uncertain count across ticks.
_payment_uncertain_monitor = PaymentUncertainMonitor()

def _billing_sweep_tick() -> None:
    """One scheduler tick: write intents for everything due now, then execute
    them against Nomba.

    NOTE: this must be the only path that calls acquire_billing_lock() for a
    given (subscription, billing_period). somba.scheduler.billing_sweep also
    exposes fetch_due_subscriptions/acquire_billing_lock and an
    emit_due_billing_events() helper that grabs the same lock but never
    writes a LedgerIntent nor charges anything -- nothing consumes its
    billing.due event. Scheduling it here would silently steal the lock from
    this real charge path and the subscription would never get billed for
    that period. Do not schedule emit_due_billing_events alongside this.
    """
    db = SessionLocal()
    try:
        charge_worker.run(db)
        charge_worker.execute_pending(db)
    except Exception:  # noqa: BLE001
        # A failing tick must never kill the scheduler — log and wait for next.
        log.exception("billing sweep tick failed")
    finally:
        db.close()


def _webhook_emitter_tick() -> None:
    """Deliver pending outbox events to merchant webhook URLs."""
    db = SessionLocal()
    try:
        emitter.run(db)
    except Exception:  # noqa: BLE001
        log.exception("webhook emitter tick failed")
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


def _queue_depth_tick() -> None:
    """Log consumer lag on the billing partition. A broker outage must never
    kill the scheduler — log and wait for next tick, same as the other jobs."""
    try:
        check_queue_depth(BILLING_CONSUMER_GROUP)
    except Exception:  # noqa: BLE001
        log.exception("queue depth tick failed")


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
        _webhook_emitter_tick,
        trigger="interval",
        seconds=30,
        id="webhook_emitter",
        max_instances=1,
        coalesce=True,
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
    scheduler.add_job(
        reconcile_sweep_tick,
        trigger="interval",
        minutes=5,
        id="reconcile_sweep",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        verify_pass_tick,
        trigger="interval",
        minutes=5,
        id="verify_pass",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        _queue_depth_tick,
        trigger="interval",
        seconds=60,
        id="queue_depth",
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
