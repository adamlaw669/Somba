"""Unit tests for the proration calculator."""

from __future__ import annotations

from datetime import datetime, timezone

from somba.subscriptions.proration import calculate

UTC = timezone.utc
JAN_1 = datetime(2026, 1, 1, tzinfo=UTC)
JAN_31 = datetime(2026, 1, 31, tzinfo=UTC)  # 30 days later


def test_upgrade_midcycle_net_positive():
    result = calculate(
        old_plan_amount=10_000,
        new_plan_amount=20_000,
        period_start=JAN_1,
        period_end=JAN_31,
        change_date=datetime(2026, 1, 16, tzinfo=UTC),  # 15 days remaining
    )
    assert result.net_kobo > 0
    assert result.charge_kobo > result.credit_kobo


def test_downgrade_midcycle_net_negative():
    result = calculate(
        old_plan_amount=20_000,
        new_plan_amount=10_000,
        period_start=JAN_1,
        period_end=JAN_31,
        change_date=datetime(2026, 1, 16, tzinfo=UTC),
    )
    assert result.net_kobo < 0
    assert result.credit_kobo > result.charge_kobo


def test_same_plan_amount_net_zero():
    result = calculate(
        old_plan_amount=10_000,
        new_plan_amount=10_000,
        period_start=JAN_1,
        period_end=JAN_31,
        change_date=datetime(2026, 1, 16, tzinfo=UTC),
    )
    assert result.net_kobo == 0


def test_all_in_kobo_integers():
    result = calculate(
        old_plan_amount=9_999,
        new_plan_amount=19_999,
        period_start=JAN_1,
        period_end=JAN_31,
        change_date=datetime(2026, 1, 10, tzinfo=UTC),
    )
    assert isinstance(result.credit_kobo, int)
    assert isinstance(result.charge_kobo, int)
    assert isinstance(result.net_kobo, int)


def test_change_at_period_start_full_charge():
    result = calculate(
        old_plan_amount=10_000,
        new_plan_amount=20_000,
        period_start=JAN_1,
        period_end=JAN_31,
        change_date=JAN_1,
    )
    # At period start, credit ≈ full old amount, charge ≈ full new amount
    assert result.remaining_days == result.total_days
    assert result.net_kobo == 10_000


def test_change_at_period_end_zero_proration():
    result = calculate(
        old_plan_amount=10_000,
        new_plan_amount=20_000,
        period_start=JAN_1,
        period_end=JAN_31,
        change_date=JAN_31,
    )
    assert result.remaining_days == 0
    assert result.credit_kobo == 0
    assert result.charge_kobo == 0
    assert result.net_kobo == 0


def test_remaining_and_total_days_populated():
    result = calculate(
        old_plan_amount=10_000,
        new_plan_amount=20_000,
        period_start=JAN_1,
        period_end=JAN_31,
        change_date=datetime(2026, 1, 16, tzinfo=UTC),
    )
    assert result.total_days == 30
    assert result.remaining_days == 15


def test_net_equals_charge_minus_credit():
    result = calculate(
        old_plan_amount=15_000,
        new_plan_amount=30_000,
        period_start=JAN_1,
        period_end=JAN_31,
        change_date=datetime(2026, 1, 11, tzinfo=UTC),
    )
    assert result.net_kobo == result.charge_kobo - result.credit_kobo
