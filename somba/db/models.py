"""Database model definitions for Somba."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def _enum(enum_cls: type[Enum]) -> SAEnum:
    return SAEnum(enum_cls, name=enum_cls.__name__.lower(), native_enum=False)


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    webhook_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    webhook_secret: Mapped[str] = mapped_column(String(255), nullable=False)

    plans: Mapped[list["Plan"]] = relationship(back_populates="merchant")
    customers: Mapped[list["Customer"]] = relationship(back_populates="merchant")


class PlanStatus(str, Enum):
    active = "active"
    archived = "archived"


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="NGN")
    interval: Mapped[str] = mapped_column(String(32), nullable=False)
    interval_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    trial_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[PlanStatus] = mapped_column(_enum(PlanStatus), nullable=False, default=PlanStatus.active)

    merchant: Mapped[Merchant] = relationship(back_populates="plans")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mandate_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bank_account_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bank_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    va_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    va_account_no: Mapped[str | None] = mapped_column(String(32), nullable=True)
    credit_balance: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    merchant: Mapped[Merchant] = relationship(back_populates="customers")


class SubscriptionStatus(str, Enum):
    trialing = "trialing"
    active = "active"
    past_due = "past_due"
    payment_uncertain = "payment_uncertain"
    paused = "paused"
    cancelled = "cancelled"
    expired = "expired"


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("merchant_id", "id", name="uq_subscriptions_merchant_id_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), index=True, nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(_enum(SubscriptionStatus), nullable=False)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_bill_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    trial_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InvoiceStatus(str, Enum):
    draft = "draft"
    open = "open"
    paid = "paid"
    void = "void"
    uncollectible = "uncollectible"


class InvoiceType(str, Enum):
    regular = "regular"
    proration = "proration"


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("subscription_id", "period_start", name="uq_invoices_subscription_period_start"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), index=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(_enum(InvoiceStatus), nullable=False)
    type: Mapped[InvoiceType] = mapped_column(_enum(InvoiceType), nullable=False, default=InvoiceType.regular)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InvoiceLineItemType(str, Enum):
    subscription = "subscription"
    proration_credit = "proration_credit"
    proration_charge = "proration_charge"


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True, nullable=False)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)
    type: Mapped[InvoiceLineItemType] = mapped_column(_enum(InvoiceLineItemType), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ChargeAttemptStatus(str, Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    uncertain = "uncertain"


class FailureClass(str, Enum):
    empty_account = "empty_account"
    broken_card = "broken_card"
    transient = "transient"
    risk = "risk"
    unknown = "unknown"


class ChargeAttempt(Base):
    __tablename__ = "charge_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), index=True, nullable=False)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    order_reference: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[ChargeAttemptStatus] = mapped_column(_enum(ChargeAttemptStatus), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    failure_class: Mapped[FailureClass | None] = mapped_column(_enum(FailureClass), nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class BillingLockStatus(str, Enum):
    locked = "locked"
    released = "released"


class BillingLock(Base):
    __tablename__ = "billing_locks"
    __table_args__ = (
        UniqueConstraint("subscription_id", "billing_period", name="uq_billing_locks_subscription_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), index=True, nullable=False)
    billing_period: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[BillingLockStatus] = mapped_column(_enum(BillingLockStatus), nullable=False)


class OutboxEventStatus(str, Enum):
    pending = "pending"
    published = "published"


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    partition_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[OutboxEventStatus] = mapped_column(_enum(OutboxEventStatus), nullable=False, default=OutboxEventStatus.pending)


class LedgerIntentStatus(str, Enum):
    pending = "pending"
    matched = "matched"
    unmatched = "unmatched"
    anomaly = "anomaly"


class LedgerIntent(Base):
    __tablename__ = "ledger_intents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), index=True, nullable=False)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True, nullable=False)
    charge_attempt_id: Mapped[int | None] = mapped_column(ForeignKey("charge_attempts.id"), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    order_reference: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[LedgerIntentStatus] = mapped_column(_enum(LedgerIntentStatus), nullable=False, default=LedgerIntentStatus.pending)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc),
    )


class LedgerSettlementSource(str, Enum):
    webhook = "webhook"
    sweep = "sweep"
    verify_pass = "verify_pass"
    transfer_push = "transfer_push"
    direct_debit = "direct_debit"


class LedgerSettlementStatus(str, Enum):
    matched = "matched"
    orphan = "orphan"
    anomaly = "anomaly"
    duplicate = "duplicate"


class LedgerSettlement(Base):
    __tablename__ = "ledger_settlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)
    intent_id: Mapped[int | None] = mapped_column(ForeignKey("ledger_intents.id"), nullable=True)
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"), nullable=True)
    order_reference: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    transaction_ref: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source: Mapped[LedgerSettlementSource] = mapped_column(_enum(LedgerSettlementSource), nullable=False)
    status: Mapped[LedgerSettlementStatus] = mapped_column(_enum(LedgerSettlementStatus), nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class SubscriptionEventTrigger(str, Enum):
    api = "api"
    scheduler = "scheduler"
    nomba_webhook = "nomba_webhook"
    reconciliation = "reconciliation"
    transfer = "transfer"


class SubscriptionEvent(Base):
    __tablename__ = "subscription_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), index=True, nullable=False)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)
    from_status: Mapped[str] = mapped_column(String(64), nullable=False)
    to_status: Mapped[str] = mapped_column(String(64), nullable=False)
    trigger: Mapped[SubscriptionEventTrigger] = mapped_column(_enum(SubscriptionEventTrigger), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class RecoveryScheduleReasonClass(str, Enum):
    empty_account = "empty_account"
    broken_card = "broken_card"
    transient = "transient"
    risk = "risk"
    unknown = "unknown"


class RecoveryScheduleStatus(str, Enum):
    scheduled = "scheduled"
    executed = "executed"
    cancelled = "cancelled"


class RecoverySchedule(Base):
    __tablename__ = "recovery_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), index=True, nullable=False)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True, nullable=False)
    charge_attempt_id: Mapped[int | None] = mapped_column(ForeignKey("charge_attempts.id"), nullable=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    reason_class: Mapped[RecoveryScheduleReasonClass] = mapped_column(_enum(RecoveryScheduleReasonClass), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[RecoveryScheduleStatus] = mapped_column(_enum(RecoveryScheduleStatus), nullable=False, default=RecoveryScheduleStatus.scheduled)


class WebhookDeliveryStatus(str, Enum):
    pending = "pending"
    delivered = "delivered"
    failed = "failed"


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)
    outbox_event_id: Mapped[int | None] = mapped_column(ForeignKey("outbox_events.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[WebhookDeliveryStatus] = mapped_column(_enum(WebhookDeliveryStatus), nullable=False, default=WebhookDeliveryStatus.pending)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IdempotencyRecordStatus(str, Enum):
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint("merchant_id", "idempotency_key", "method", "path", name="uq_idempotency_records_lookup"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[IdempotencyRecordStatus] = mapped_column(_enum(IdempotencyRecordStatus), nullable=False, default=IdempotencyRecordStatus.in_progress)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
