"""Shared API error helpers for consistent JSON error responses."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi.responses import JSONResponse


@dataclass
class APIError(Exception):
    """Application error with a machine-readable code and HTTP status."""

    code: str
    message: str
    status_code: int = 400
    param: str | None = None


def error_response(error: APIError) -> JSONResponse:
    """Render API errors in the documented response shape."""

    payload = {
        "error": {
            "code": error.code,
            "message": error.message,
        }
    }
    if error.param is not None:
        payload["error"]["param"] = error.param
    return JSONResponse(status_code=error.status_code, content=payload)
