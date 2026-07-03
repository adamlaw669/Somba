"""Sandbox connectivity checks against Nomba — always uses the dedicated
TEST credentials and the sandbox host, regardless of what NOMBA_CLIENT_ID /
NOMBA_API_BASE_URL are currently set to in the main environment. Safe to hit
even when the account is holding live credentials.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from somba.api.errors import APIError
from somba.api.middleware.auth import get_current_merchant
from somba.db.models import Merchant
from somba.db.session import get_db
from somba.nomba.sandbox_client import (
    SandboxNombaError,
    sandbox_create_virtual_account,
    sandbox_issue_token,
)

router = APIRouter(prefix="/v1/sandbox/nomba", tags=["sandbox"])


def _raise_from(exc: SandboxNombaError) -> None:
    raise APIError(
        code="sandbox_nomba_error",
        message=str(exc),
        status_code=502,
    ) from exc


@router.post("/auth")
def check_auth(
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    """Confirm the sandbox TEST credentials can issue a token."""

    try:
        sandbox_issue_token()
    except SandboxNombaError as exc:
        _raise_from(exc)
    return {"status": "ok", "environment": "sandbox"}


class SandboxVirtualAccountRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=255)


@router.post("/virtual-account")
def check_virtual_account(
    body: SandboxVirtualAccountRequest,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    """Create a throwaway virtual account in Nomba's sandbox to confirm the
    full auth + resource-call path works. Never touches live credentials."""

    try:
        va = sandbox_create_virtual_account(customer_name=body.customer_name)
    except SandboxNombaError as exc:
        _raise_from(exc)
    return {
        "status": "ok",
        "environment": "sandbox",
        "account_number": va.account_number,
        "bank_name": va.bank_name,
        "account_holder_id": va.account_holder_id,
        "account_ref": va.account_ref,
    }
