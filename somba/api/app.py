"""FastAPI application for Somba."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from somba.api.errors import APIError, error_response
from somba.api.middleware.auth import get_current_merchant
from somba.api.middleware.idempotency import IdempotencyMiddleware
from somba.db.models import Merchant
from somba.db.session import get_db, init_db

app = FastAPI(title="Somba")
app.add_middleware(IdempotencyMiddleware)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.exception_handler(APIError)
async def api_error_handler(_: Request, exc: APIError) -> JSONResponse:
    return error_response(exc)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "param": None,
            }
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/me")
def me(current_merchant: Merchant = Depends(get_current_merchant)) -> dict[str, object]:
    return {
        "merchant": {
            "id": current_merchant.id,
            "name": current_merchant.name,
            "api_key_id": current_merchant.api_key_id,
            "webhook_url": current_merchant.webhook_url,
        }
    }


@app.get("/v1/db-status")
def db_status(db: Session = Depends(get_db)) -> dict[str, str]:
    """A lightweight check that the database session is wired."""

    db.execute(text("SELECT 1"))
    return {"status": "database_connected"}
