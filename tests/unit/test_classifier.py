"""Unit tests for the failure classifier."""

from __future__ import annotations

import pytest

from somba.db.models import FailureClass
from somba.workers.recovery.classifier import classify


@pytest.mark.parametrize("code,expected", [
    ("51", FailureClass.empty_account),
    ("61", FailureClass.empty_account),
    ("65", FailureClass.empty_account),
    ("54", FailureClass.broken_card),
    ("55", FailureClass.broken_card),
    ("14", FailureClass.broken_card),
    ("06", FailureClass.transient),
    ("91", FailureClass.transient),
    ("96", FailureClass.transient),
    ("34", FailureClass.risk),
    ("38", FailureClass.risk),
    ("43", FailureClass.risk),
])
def test_classify_by_response_code(code, expected):
    assert classify(code, None) == expected


@pytest.mark.parametrize("reason,expected", [
    ("Insufficient funds in account", FailureClass.empty_account),
    ("Expired card", FailureClass.broken_card),
    ("System timeout, please try again", FailureClass.transient),
    ("Suspected fraud detected", FailureClass.risk),
    ("Some totally unknown reason", FailureClass.unknown),
])
def test_classify_by_keyword_fallback(reason, expected):
    assert classify(None, reason) == expected


def test_code_takes_precedence_over_keyword():
    # Code says transient, keyword says empty — code wins
    assert classify("91", "insufficient funds") == FailureClass.transient


def test_empty_inputs_return_unknown():
    assert classify(None, None) == FailureClass.unknown
    assert classify("", "") == FailureClass.unknown
