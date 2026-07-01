"""Reconciliation scheduler ticks: periodic sweep + verify pass."""

from __future__ import annotations

import logging

from somba.db.session import SessionLocal
from somba.workers.reconcile import sweep, verify_pass

log = logging.getLogger(__name__)


def reconcile_sweep_tick() -> None:
    """Fetch recent Nomba transactions and match against pending intents."""
    db = SessionLocal()
    try:
        resolved = sweep.run(db)
        log.info("reconcile.sweep tick: resolved=%d", resolved)
    except Exception:
        log.exception("reconcile sweep tick failed")
    finally:
        db.close()


def verify_pass_tick() -> None:
    """Query Nomba to resolve payment_uncertain subscriptions."""
    db = SessionLocal()
    try:
        resolved = verify_pass.run(db)
        log.info("verify_pass tick: resolved=%d", resolved)
    except Exception:
        log.exception("verify_pass tick failed")
    finally:
        db.close()
