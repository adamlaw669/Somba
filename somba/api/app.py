"""FastAPI application for Somba."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from somba.api.customers import router as customers_router
from somba.api.errors import APIError, error_response
from somba.api.middleware.auth import get_current_merchant
from somba.api.middleware.idempotency import IdempotencyMiddleware
from somba.api.plans import router as plans_router
from somba.api.subscriptions import router as subscriptions_router
from somba.api.webhooks import router as webhooks_router
from somba.db.models import Merchant
from somba.db.session import get_db, init_db
from somba.security import generate_api_key_material

app = FastAPI(title="Somba")
app.add_middleware(IdempotencyMiddleware)
app.include_router(webhooks_router)
app.include_router(plans_router)
app.include_router(customers_router)
app.include_router(subscriptions_router)


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


class MerchantCreateRequest(BaseModel):
    name: str
    webhook_url: str | None = None
    webhook_secret: str = ""


@app.post("/v1/merchants", status_code=201)
def create_merchant(
    body: MerchantCreateRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    key = generate_api_key_material()
    merchant = Merchant(
        name=body.name,
        api_key_id=key.public_id,
        api_key_hash=key.secret_hash,
        webhook_url=body.webhook_url,
        webhook_secret=body.webhook_secret,
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return {
        "merchant": {
            "id": merchant.id,
            "name": merchant.name,
            "webhook_url": merchant.webhook_url,
        },
        "api_key": key.token,
    }


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
