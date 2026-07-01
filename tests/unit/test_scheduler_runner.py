"""Scheduler wiring: guards a real production bug found while deploying.

somba.scheduler.billing_sweep.emit_due_billing_events() and
somba.workers.charge.worker.run() both call acquire_billing_lock() for the
same (subscription_id, billing_period) key. Only one of them may ever be
scheduled: emit_due_billing_events() grabs the lock and writes a billing.due
OutboxEvent that nothing consumes, while charge_worker.run() is the one that
actually writes the LedgerIntent and gets the subscription charged. If both
were scheduled, whichever fires first on a given day permanently locks the
other out for that day -- subscriptions would silently never be billed.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from somba.scheduler import runner


def test_scheduler_registers_expected_jobs():
    scheduler = runner.build_scheduler()
    job_ids = {job.id for job in scheduler.get_jobs()}

    assert job_ids == {
        "billing_sweep",
        "webhook_emitter",
        "pending_intent_alert",
        "payment_uncertain_alert",
        "reconcile_sweep",
        "verify_pass",
        "queue_depth",
    }


def test_billing_sweep_tick_calls_charge_worker_phase1_and_phase2(monkeypatch):
    fake_db = MagicMock()
    monkeypatch.setattr(runner, "SessionLocal", lambda: fake_db)

    calls = []
    monkeypatch.setattr(runner.charge_worker, "run", lambda db: calls.append(("run", db)))
    monkeypatch.setattr(runner.charge_worker, "execute_pending", lambda db: calls.append(("execute_pending", db)))

    runner._billing_sweep_tick()

    assert calls == [("run", fake_db), ("execute_pending", fake_db)]
    fake_db.close.assert_called_once()


def test_billing_sweep_tick_never_calls_emit_due_billing_events(monkeypatch):
    """Regression guard: this function must not be reintroduced into the tick --
    it silently steals the billing lock from the real charge path (see module
    docstring). Scheduling both would mean subscriptions never get charged."""
    fake_db = MagicMock()
    monkeypatch.setattr(runner, "SessionLocal", lambda: fake_db)

    from somba.scheduler import billing_sweep

    called = []
    monkeypatch.setattr(billing_sweep, "emit_due_billing_events", lambda *a, **k: called.append(True))

    runner._billing_sweep_tick()

    assert called == []


def test_webhook_emitter_tick_calls_emitter_run(monkeypatch):
    fake_db = MagicMock()
    monkeypatch.setattr(runner, "SessionLocal", lambda: fake_db)

    calls = []
    monkeypatch.setattr(runner.emitter, "run", lambda db: calls.append(db))

    runner._webhook_emitter_tick()

    assert calls == [fake_db]
    fake_db.close.assert_called_once()


def test_billing_sweep_tick_failure_does_not_raise(monkeypatch):
    """A failing tick must never kill the scheduler process."""
    fake_db = MagicMock()
    monkeypatch.setattr(runner, "SessionLocal", lambda: fake_db)
    monkeypatch.setattr(runner.charge_worker, "run", MagicMock(side_effect=RuntimeError("boom")))

    runner._billing_sweep_tick()  # must not raise

    fake_db.close.assert_called_once()
