"""FastAPI application for Somba."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from somba.api.auth import router as auth_router
from somba.api.customers import router as customers_router
from somba.api.errors import APIError, error_response
from somba.api.events import router as events_router
from somba.api.invoices import router as invoices_router
from somba.api.metrics import router as metrics_router
from somba.api.middleware.auth import get_current_merchant
from somba.api.middleware.idempotency import IdempotencyMiddleware
from somba.api.plans import router as plans_router
from somba.api.sandbox import router as sandbox_router
from somba.api.subscriptions import router as subscriptions_router
from somba.api.webhooks import router as webhooks_router
from somba.db.models import Merchant
from somba.db.session import get_db, init_db

app = FastAPI(title="Somba")
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(webhooks_router)
app.include_router(plans_router)
app.include_router(customers_router)
app.include_router(subscriptions_router)
app.include_router(invoices_router)
app.include_router(events_router)
app.include_router(metrics_router)
app.include_router(sandbox_router)


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
            "webhook_url": current_merchant.webhook_url,
        }
    }


@app.get("/v1/db-status")
def db_status(db: Session = Depends(get_db)) -> dict[str, str]:
    """A lightweight check that the database session is wired."""

    db.execute(text("SELECT 1"))
    return {"status": "database_connected"}
