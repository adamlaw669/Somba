"""Unit tests for the recovery engine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from somba.db.models import (
    Base,
    Customer,
    FailureClass,
    Merchant,
    OutboxEvent,
    Plan,
    RecoverySchedule,
    RecoveryScheduleStatus,
    Subscription,
    SubscriptionStatus,
)
from somba.nomba.client import VirtualAccountResult
from somba.workers.recovery import engine as recovery_engine
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


# ---------------------------------------------------------------------------
# Transfer path: virtual account issuance
# ---------------------------------------------------------------------------


def _make_real_subscription(db, *, customer_name: str | None = "Real Customer") -> Subscription:
    merchant = Merchant(
        name="M", api_key_id="k" * 16, api_key_hash="h", webhook_secret="s",
    )
    db.add(merchant)
    db.flush()
    plan = Plan(merchant_id=merchant.id, name="P", amount=1000, currency="NGN", interval="month")
    db.add(plan)
    db.flush()
    customer = Customer(merchant_id=merchant.id, name=customer_name)
    db.add(customer)
    db.flush()
    sub = Subscription(
        merchant_id=merchant.id, customer_id=customer.id, plan_id=plan.id,
        status=SubscriptionStatus.active,
    )
    db.add(sub)
    db.flush()
    return sub


def _run_for_sub(db, sub, failure_class, attempt_number=1):
    return recovery_run(
        db,
        merchant_id=sub.merchant_id,
        subscription_id=sub.id,
        invoice_id=20,
        charge_attempt_id=30,
        failure_class=failure_class,
        attempt_number=attempt_number,
        now=NOW,
    )


def test_transfer_path_issues_virtual_account_and_stores_on_customer(db, monkeypatch):
    sub = _make_real_subscription(db)
    monkeypatch.setattr(
        recovery_engine.nomba_client, "create_virtual_account",
        lambda **kwargs: VirtualAccountResult(
            account_number="1234567890", bank_name="Nombank MFB",
            account_holder_id="holder-1", account_ref="ref-1",
        ),
    )

    _run_for_sub(db, sub, FailureClass.risk)
    db.flush()

    customer = db.get(Customer, sub.customer_id)
    assert customer.va_account_no == "1234567890"
    assert customer.va_id == "holder-1"

    event = db.scalar(select(OutboxEvent))
    assert event.payload["virtual_account"] == {"account_number": "1234567890", "bank_name": "Nombank MFB"}


def test_transfer_path_reuses_existing_virtual_account(db, monkeypatch):
    sub = _make_real_subscription(db)
    customer = db.get(Customer, sub.customer_id)
    customer.va_account_no = "already-issued"
    db.flush()

    calls = []
    monkeypatch.setattr(
        recovery_engine.nomba_client, "create_virtual_account",
        lambda **kwargs: calls.append(1) or VirtualAccountResult("new", "bank", "id", "ref"),
    )

    _run_for_sub(db, sub, FailureClass.risk)
    db.flush()

    assert calls == []  # never called -- reused the existing VA
    event = db.scalar(select(OutboxEvent))
    assert event.payload["virtual_account"] == {"account_number": "already-issued"}


def test_transfer_path_survives_virtual_account_creation_failure(db, monkeypatch):
    """Nomba VA creation failing must not break the transfer_required event."""
    sub = _make_real_subscription(db)

    def boom(**kwargs):
        raise RuntimeError("nomba unreachable")

    monkeypatch.setattr(recovery_engine.nomba_client, "create_virtual_account", boom)

    action = _run_for_sub(db, sub, FailureClass.risk)
    db.flush()

    assert action == "transfer"
    event = db.scalar(select(OutboxEvent))
    assert event.event_type == "subscription.transfer_required"
    assert "virtual_account" not in event.payload

    customer = db.get(Customer, sub.customer_id)
    assert customer.va_account_no is None


def test_transfer_path_short_customer_name_falls_back(db, monkeypatch):
    """Nomba requires accountName >= 8 chars; a short/blank name must not 400."""
    sub = _make_real_subscription(db, customer_name="Al")  # too short

    captured = {}

    def fake_create(*, customer_name, base_url=None):
        captured["name"] = customer_name
        return VirtualAccountResult("123", "bank", "id", "ref")

    monkeypatch.setattr(recovery_engine.nomba_client, "create_virtual_account", fake_create)

    _run_for_sub(db, sub, FailureClass.risk)

    assert len(captured["name"]) >= 8
