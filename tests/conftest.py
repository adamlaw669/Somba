"""Shared fixtures for all test suites."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from somba.db.models import Base, Customer, Merchant, Plan, PlanStatus, Subscription, SubscriptionStatus
from somba.security import generate_api_key_material


@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db(db_engine) -> Session:
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def make_merchant(db):
    """Factory: create and persist a merchant, return (merchant, raw_token)."""
    def _make(name: str = "Test Merchant") -> tuple[Merchant, str]:
        key = generate_api_key_material()
        m = Merchant(
            name=name,
            api_key_id=key.public_id,
            api_key_hash=key.secret_hash,
            webhook_url=None,
            webhook_secret="whsec_test",
        )
        db.add(m)
        db.commit()
        db.refresh(m)
        return m, key.token

    return _make


@pytest.fixture
def merchant_and_token(make_merchant):
    return make_merchant()


@pytest.fixture
def make_plan(db):
    """Factory: create and persist a plan for a given merchant."""
    def _make(
        merchant: Merchant,
        *,
        name: str = "Monthly",
        amount: int = 10_000,
        interval: str = "month",
        status: PlanStatus = PlanStatus.active,
    ) -> Plan:
        plan = Plan(
            merchant_id=merchant.id,
            name=name,
            amount=amount,
            currency="NGN",
            interval=interval,
            interval_count=1,
            trial_days=0,
            status=status,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    return _make


@pytest.fixture
def make_customer(db):
    """Factory: create and persist a customer for a given merchant."""
    def _make(merchant: Merchant, *, email: str = "test@example.com") -> Customer:
        customer = Customer(
            merchant_id=merchant.id,
            email=email,
            name="Test User",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    return _make


@pytest.fixture
def make_subscription(db):
    """Factory: create and persist a subscription."""
    def _make(
        merchant: Merchant,
        customer: Customer,
        plan: Plan,
        *,
        status: SubscriptionStatus = SubscriptionStatus.active,
        next_bill_date=None,
        current_period_start=None,
        current_period_end=None,
    ) -> Subscription:
        sub = Subscription(
            merchant_id=merchant.id,
            customer_id=customer.id,
            plan_id=plan.id,
            status=status,
            next_bill_date=next_bill_date,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    return _make


def idem_key() -> str:
    return uuid.uuid4().hex
