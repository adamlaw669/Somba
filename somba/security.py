"""Helpers for API key creation, parsing, hashing, and verification."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

import bcrypt

API_KEY_PREFIX = "sk-somba-"


@dataclass(frozen=True)
class APIKeyMaterial:
    """Convenience container for generated API key material."""

    public_id: str
    secret: str
    token: str
    secret_hash: str


def generate_api_key_material() -> APIKeyMaterial:
    """Generate a merchant API key that starts with the Somba prefix."""

    public_id = secrets.token_hex(8)
    secret = secrets.token_urlsafe(32)
    token = f"{API_KEY_PREFIX}{public_id}.{secret}"
    return APIKeyMaterial(
        public_id=public_id,
        secret=secret,
        token=token,
        secret_hash=hash_api_key_secret(secret),
    )


def parse_api_key(token: str) -> tuple[str, str]:
    """Split a bearer token into public id and secret."""

    if not token.startswith(API_KEY_PREFIX):
        raise ValueError("API key must start with sk-somba-")

    body = token[len(API_KEY_PREFIX) :]
    if "." not in body:
        raise ValueError("API key must include a public id and secret")

    public_id, secret = body.split(".", 1)
    if not public_id or not secret:
        raise ValueError("API key is missing a public id or secret")
    return public_id, secret


def hash_api_key_secret(secret: str) -> str:
    """Hash the secret portion of an API key with bcrypt."""

    return bcrypt.hashpw(secret.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_api_key_secret(secret: str, secret_hash: str) -> bool:
    """Check whether a secret matches a stored bcrypt hash."""

    try:
        return bcrypt.checkpw(secret.encode("utf-8"), secret_hash.encode("utf-8"))
    except ValueError:
        return False
