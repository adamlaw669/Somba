"""Map a Nomba failure reason / response code to a FailureClass enum value."""

from __future__ import annotations

from somba.db.models import FailureClass

# ISO 8583 response codes as returned in Nomba charge responses
_EMPTY_ACCOUNT_CODES = {"51", "61", "65"}
_BROKEN_CARD_CODES = {"14", "54", "55", "57", "58", "62", "89"}
_TRANSIENT_CODES = {"06", "91", "96", "97"}
_RISK_CODES = {"34", "38", "41", "43", "63"}

# Substring patterns in the failure_reason string (lower-cased)
_EMPTY_ACCOUNT_KEYWORDS = {"insufficient", "no funds", "balance", "empty"}
_BROKEN_CARD_KEYWORDS = {"expired", "invalid card", "invalid account", "do not honour", "not permitted"}
_TRANSIENT_KEYWORDS = {"timeout", "processing error", "try again", "temporary", "system error"}
_RISK_KEYWORDS = {"fraud", "security", "stolen", "lost card", "suspected"}


def classify(response_code: str | None, failure_reason: str | None) -> FailureClass:
    """Return the FailureClass that best matches the Nomba failure signal."""
    code = (response_code or "").strip()
    reason_lc = (failure_reason or "").lower()

    if code in _EMPTY_ACCOUNT_CODES:
        return FailureClass.empty_account
    if code in _BROKEN_CARD_CODES:
        return FailureClass.broken_card
    if code in _TRANSIENT_CODES:
        return FailureClass.transient
    if code in _RISK_CODES:
        return FailureClass.risk

    # Fall back to keyword matching when the code is absent or unrecognised
    if any(kw in reason_lc for kw in _EMPTY_ACCOUNT_KEYWORDS):
        return FailureClass.empty_account
    if any(kw in reason_lc for kw in _BROKEN_CARD_KEYWORDS):
        return FailureClass.broken_card
    if any(kw in reason_lc for kw in _TRANSIENT_KEYWORDS):
        return FailureClass.transient
    if any(kw in reason_lc for kw in _RISK_KEYWORDS):
        return FailureClass.risk

    return FailureClass.unknown
