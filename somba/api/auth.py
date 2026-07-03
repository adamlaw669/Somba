"""Dashboard authentication: email/password signup and login, session-scoped
merchant lookup, and minting the named API keys merchants use in their own
code.

This is deliberately a separate credential from API keys. Email/password
gets a merchant into the dashboard; API keys are things they mint from
inside it and use in their own backend. Revoking one key, or ending a
session, never touches the others.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.api.errors import APIError
from somba.db.models import ApiKey, Merchant, MerchantSession
from somba.db.session import get_db
from somba.security import (
    generate_api_key_material,
    generate_session_token,
    hash_password,
    parse_session_token,
    verify_api_key_secret,
    verify_password,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])


def _merchant_to_dict(merchant: Merchant) -> dict:
    return {"id": merchant.id, "name": merchant.name, "email": merchant.email}


def _api_key_to_dict(key: ApiKey) -> dict:
    return {
        "id": key.id,
        "name": key.name,
        "key_id": key.key_id,
        "created_at": key.created_at.isoformat() if key.created_at else None,
        "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
    }


def _issue_session(db: Session, merchant: Merchant) -> str:
    token = generate_session_token()
    db.add(
        MerchantSession(
            merchant_id=merchant.id,
            session_id=token.session_id,
            session_secret_hash=token.secret_hash,
        )
    )
    db.commit()
    return token.token


def get_current_dashboard_merchant(
    request: Request,
    db: Session = Depends(get_db),
) -> Merchant:
    """Resolve the current merchant from a dashboard session bearer token."""

    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise APIError(code="unauthorized", message="Missing session token", status_code=401)
    token = header.removeprefix("Bearer ").strip()

    try:
        session_id, secret = parse_session_token(token)
    except ValueError as exc:
        raise APIError(code="invalid_session", message=str(exc), status_code=401) from exc

    session = db.scalar(
        select(MerchantSession).where(MerchantSession.session_id == session_id)
    )
    if session is None or not verify_api_key_secret(secret, session.session_secret_hash):
        raise APIError(code="invalid_session", message="Invalid or expired session", status_code=401)

    merchant = db.get(Merchant, session.merchant_id)
    if merchant is None:
        raise APIError(code="invalid_session", message="Invalid or expired session", status_code=401)
    return merchant


def _get_api_key_or_404(db: Session, key_row_id: int, merchant: Merchant) -> ApiKey:
    key = db.scalar(
        select(ApiKey).where(
            ApiKey.id == key_row_id,
            ApiKey.merchant_id == merchant.id,
            ApiKey.revoked_at.is_(None),
        )
    )
    if key is None:
        raise APIError(code="not_found", message="API key not found", status_code=404)
    return key


class SignupRequest(BaseModel):
    name: str = Field(max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(max_length=255)


@router.post("/signup", status_code=201)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> dict:
    existing = db.scalar(select(Merchant).where(Merchant.email == body.email))
    if existing is not None:
        raise APIError(code="email_taken", message="An account with this email already exists", status_code=409)

    merchant = Merchant(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)

    session_token = _issue_session(db, merchant)
    return {"merchant": _merchant_to_dict(merchant), "session_token": session_token}


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)) -> dict:
    merchant = db.scalar(select(Merchant).where(Merchant.email == body.email))
    if merchant is None or merchant.password_hash is None or not verify_password(
        body.password, merchant.password_hash
    ):
        raise APIError(code="invalid_credentials", message="Invalid email or password", status_code=401)

    session_token = _issue_session(db, merchant)
    return {"merchant": _merchant_to_dict(merchant), "session_token": session_token}


@router.get("/me")
def me(merchant: Merchant = Depends(get_current_dashboard_merchant)) -> dict:
    return {"merchant": _merchant_to_dict(merchant)}


@router.get("/api-keys")
def list_api_keys(
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_dashboard_merchant),
) -> dict:
    keys = list(
        db.scalars(
            select(ApiKey)
            .where(ApiKey.merchant_id == merchant.id, ApiKey.revoked_at.is_(None))
            .order_by(ApiKey.created_at.desc())
        )
    )
    return {"api_keys": [_api_key_to_dict(k) for k in keys]}


@router.post("/api-keys", status_code=201)
def create_api_key(
    body: ApiKeyCreateRequest,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_dashboard_merchant),
) -> dict:
    """Mint a new named API key for the merchant. Existing keys are untouched."""

    material = generate_api_key_material()
    key = ApiKey(
        merchant_id=merchant.id,
        name=body.name,
        key_id=material.public_id,
        key_hash=material.secret_hash,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return {**_api_key_to_dict(key), "api_key": material.token}


@router.delete("/api-keys/{key_row_id}")
def revoke_api_key(
    key_row_id: int,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_dashboard_merchant),
) -> dict:
    key = _get_api_key_or_404(db, key_row_id, merchant)
    key.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": key.id, "revoked": True}
