"""Idempotency validation middleware for mutating API requests."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from somba.api.errors import APIError, error_response

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Require an idempotency key for mutating requests."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        if request.method in MUTATING_METHODS:
            key = request.headers.get("Idempotency-Key", "").strip()
            if not key:
                error = APIError(
                    code="missing_idempotency_key",
                    message="Mutating requests require an Idempotency-Key header",
                    status_code=400,
                    param="Idempotency-Key",
                )
                return error_response(error)
            request.state.idempotency_key = key

        return await call_next(request)
