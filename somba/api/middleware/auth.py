"""Authentication helpers for bearer API keys."""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.api.errors import APIError
from somba.db.models import Merchant
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

    merchant = db.scalar(select(Merchant).where(Merchant.api_key_id == public_id))
    if merchant is None or not verify_api_key_secret(secret, merchant.api_key_hash):
        raise APIError(
            code="invalid_api_key",
            message="Invalid API key",
            status_code=401,
        )
    return merchant
