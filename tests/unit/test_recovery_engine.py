"""Unit tests for the recovery engine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from somba.db.models import Base, FailureClass, OutboxEvent, RecoverySchedule, RecoveryScheduleStatus
from somba.workers.recovery.engine import run as recovery_run

UTC = timezone.utc
NOW = datetime(2026, 6, 29, 10, 0, 0, tzinfo=UTC)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False)
    sess = SessionLocal()
    try:
        yield sess
    finally:
        sess.close()


def _run(db, failure_class, attempt_number=1):
    return recovery_run(
        db,
        merchant_id=1,
        subscription_id=10,
        invoice_id=20,
        charge_attempt_id=30,
        failure_class=failure_class,
        attempt_number=attempt_number,
        now=NOW,
    )


# ---------------------------------------------------------------------------
# Timing path
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fc", [FailureClass.empty_account, FailureClass.unknown])
def test_timing_path_writes_recovery_schedule(db, fc):
    action = _run(db, fc)
    db.flush()
    assert action == "timing"
    schedules = list(db.scalars(select(RecoverySchedule)))
    assert len(schedules) == 1
    assert schedules[0].status == RecoveryScheduleStatus.scheduled
    assert schedules[0].subscription_id == 10
    assert schedules[0].attempt_number == 2


def test_transient_first_attempt_is_timing(db):
    action = _run(db, FailureClass.transient, attempt_number=1)
    db.flush()
    assert action == "timing"
    assert db.query(RecoverySchedule).count() == 1


def test_timing_scheduled_for_is_in_the_future(db):
    _run(db, FailureClass.empty_account, attempt_number=1)
    db.flush()
    sched = db.scalar(select(RecoverySchedule))
    # SQLite returns naive datetimes; strip tz from NOW for comparison
    now_naive = NOW.replace(tzinfo=None)
    assert sched.scheduled_for > now_naive


def test_empty_account_delay_grows_with_attempt(db):
    _run(db, FailureClass.empty_account, attempt_number=1)
    _run(db, FailureClass.empty_account, attempt_number=2)
    db.flush()
    schedules = sorted(db.scalars(select(RecoverySchedule)).all(), key=lambda s: s.attempt_number)
    assert schedules[0].scheduled_for < schedules[1].scheduled_for


# ---------------------------------------------------------------------------
# Transfer path
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fc", [FailureClass.broken_card, FailureClass.risk])
def test_transfer_path_writes_outbox_event(db, fc):
    action = _run(db, fc)
    db.flush()
    assert action == "transfer"
    events = list(db.scalars(select(OutboxEvent)))
    assert len(events) == 1
    assert events[0].event_type == "subscription.transfer_required"


def test_transient_second_attempt_switches_to_transfer(db):
    action = _run(db, FailureClass.transient, attempt_number=2)
    db.flush()
    assert action == "transfer"
    assert db.query(OutboxEvent).count() == 1


def test_transfer_path_writes_no_recovery_schedule(db):
    _run(db, FailureClass.risk)
    db.flush()
    assert db.query(RecoverySchedule).count() == 0
