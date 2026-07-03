"""Authentication helpers for bearer API keys."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.api.errors import APIError
from somba.db.models import ApiKey, Merchant
from somba.db.session import get_db
from somba.security import parse_api_key, verify_api_key_secret


def get_bearer_token(request: Request) -> str:
    """Extract a bearer token from the Authorization header."""

    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise APIError(
            code="unauthorized",
            message="Missing bearer token",
            status_code=401,
        )
    return header.removeprefix("Bearer ").strip()


def get_current_merchant(
    request: Request,
    db: Session = Depends(get_db),
) -> Merchant:
    """Resolve the current merchant from the bearer token."""

    token = get_bearer_token(request)

    try:
        public_id, secret = parse_api_key(token)
    except ValueError as exc:
        raise APIError(
            code="invalid_api_key",
            message=str(exc),
            status_code=401,
        ) from exc

    api_key = db.scalar(
        select(ApiKey).where(ApiKey.key_id == public_id, ApiKey.revoked_at.is_(None))
    )
    if api_key is None or not verify_api_key_secret(secret, api_key.key_hash):
        raise APIError(
            code="invalid_api_key",
            message="Invalid API key",
            status_code=401,
        )

    merchant = db.get(Merchant, api_key.merchant_id)
    if merchant is None:
        raise APIError(
            code="invalid_api_key",
            message="Invalid API key",
            status_code=401,
        )

    api_key.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return merchant
