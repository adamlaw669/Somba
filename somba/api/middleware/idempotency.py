"""Idempotency middleware.

Requires an Idempotency-Key on mutating requests, and — for authenticated
requests — stores the response the first time a key is seen and *replays* it
when the same key is reused. This makes POST/PATCH/DELETE safe to retry:

  - same key + same request body   -> the stored response is replayed
  - same key + different body       -> 409 (the key was reused for a new request)
  - key still in flight             -> 409 (a concurrent request holds it)

The store lives in idempotency_records (one row per merchant+key+method+path).
"""

from __future__ import annotations

import hashlib
import json
import logging

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from somba.api.errors import APIError, error_response
from somba.db.models import ApiKey, IdempotencyRecord, IdempotencyRecordStatus
from somba.db.session import get_db
from somba.security import parse_api_key, verify_api_key_secret

log = logging.getLogger(__name__)

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
IDEMPOTENCY_EXEMPT = {"/v1/webhooks/nomba"}
IDEMPOTENCY_EXEMPT_PREFIXES = ("/v1/auth/",)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Require an idempotency key and replay stored responses on repeat keys."""

    async def dispatch(self, request: Request, call_next):
        exempt = request.url.path in IDEMPOTENCY_EXEMPT or request.url.path.startswith(
            IDEMPOTENCY_EXEMPT_PREFIXES
        )
        if request.method not in MUTATING_METHODS or exempt:
            return await call_next(request)

        key = request.headers.get("Idempotency-Key", "").strip()
        if not key:
            return error_response(
                APIError(
                    code="missing_idempotency_key",
                    message="Mutating requests require an Idempotency-Key header",
                    status_code=400,
                    param="Idempotency-Key",
                )
            )
        request.state.idempotency_key = key

        merchant_id = self._resolve_merchant_id(request)
        if merchant_id is None:
            # Unauthenticated / invalid key: let the route's auth return 401.
            return await call_next(request)

        # Reading the body here is safe — Starlette's BaseHTTPMiddleware caches
        # it and replays it to the downstream handler.
        body = await request.body()
        request_hash = hashlib.sha256(
            request.method.encode() + b"|" + request.url.path.encode() + b"|" + body
        ).hexdigest()
        lookup = (merchant_id, key, request.method, request.url.path)

        # --- claim the key, or replay an existing result ---
        db, gen = self._session(request)
        try:
            existing = self._fetch(db, lookup)
            if existing is not None:
                replay = self._maybe_replay(existing, request_hash)
                if replay is not None:
                    return replay
                # A 'failed' record: drop it and let this attempt retry.
                db.delete(existing)
                db.commit()

            db.add(
                IdempotencyRecord(
                    merchant_id=merchant_id,
                    idempotency_key=key,
                    method=request.method,
                    path=request.url.path,
                    request_hash=request_hash,
                    status=IdempotencyRecordStatus.in_progress,
                )
            )
            try:
                db.commit()
            except IntegrityError:
                # A concurrent request claimed the same key first.
                db.rollback()
                return self._conflict("A request with this Idempotency-Key is already in progress")
        finally:
            self._close(gen)

        # --- run the real handler ---
        try:
            response = await call_next(request)
        except Exception:
            # Handler blew up: release the key so the client can retry.
            self._release(request, lookup)
            raise

        raw = b"".join([chunk async for chunk in response.body_iterator])

        # --- persist the response (2xx) or release the key (anything else) ---
        db, gen = self._session(request)
        try:
            rec = self._fetch(db, lookup)
            if rec is not None:
                if 200 <= response.status_code < 300:
                    rec.status = IdempotencyRecordStatus.completed
                    rec.response_status = response.status_code
                    rec.response_body = _safe_json(raw)
                else:
                    db.delete(rec)
                db.commit()
        finally:
            self._close(gen)

        headers = dict(response.headers)
        headers.pop("content-length", None)
        return Response(
            content=raw,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )

    # ------------------------------------------------------------------ helpers

    def _session(self, request: Request):
        """Resolve a DB session the same way FastAPI does — honouring overrides."""
        dep = request.app.dependency_overrides.get(get_db, get_db)
        gen = dep()
        return next(gen), gen

    @staticmethod
    def _close(gen) -> None:
        try:
            next(gen)
        except StopIteration:
            pass

    @staticmethod
    def _fetch(db, lookup):
        merchant_id, key, method, path = lookup
        return db.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.merchant_id == merchant_id,
                IdempotencyRecord.idempotency_key == key,
                IdempotencyRecord.method == method,
                IdempotencyRecord.path == path,
            )
        )

    def _release(self, request: Request, lookup) -> None:
        db, gen = self._session(request)
        try:
            rec = self._fetch(db, lookup)
            if rec is not None:
                db.delete(rec)
                db.commit()
        finally:
            self._close(gen)

    def _resolve_merchant_id(self, request: Request) -> int | None:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return None
        token = header.removeprefix("Bearer ").strip()
        try:
            public_id, secret = parse_api_key(token)
        except ValueError:
            return None
        db, gen = self._session(request)
        try:
            api_key = db.scalar(
                select(ApiKey).where(ApiKey.key_id == public_id, ApiKey.revoked_at.is_(None))
            )
            if api_key is None or not verify_api_key_secret(secret, api_key.key_hash):
                return None
            return api_key.merchant_id
        finally:
            self._close(gen)

    def _maybe_replay(self, existing: IdempotencyRecord, request_hash: str):
        if existing.status == IdempotencyRecordStatus.completed:
            if existing.request_hash == request_hash:
                body = existing.response_body
                content = json.dumps(body).encode() if body is not None else b""
                resp = Response(
                    content=content,
                    status_code=existing.response_status or 200,
                    media_type="application/json",
                )
                resp.headers["Idempotency-Replayed"] = "true"
                return resp
            return self._conflict(
                "Idempotency-Key was reused with a different request body",
                code="idempotency_key_reuse",
            )
        if existing.status == IdempotencyRecordStatus.in_progress:
            return self._conflict("A request with this Idempotency-Key is already in progress")
        return None  # failed -> caller drops it and retries

    @staticmethod
    def _conflict(message: str, code: str = "idempotency_conflict"):
        return error_response(
            APIError(code=code, message=message, status_code=409, param="Idempotency-Key")
        )


def _safe_json(raw: bytes):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return None
