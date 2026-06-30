"""Invoice read endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.api.errors import APIError
from somba.api.middleware.auth import get_current_merchant
from somba.db.models import Invoice, InvoiceLineItem, Merchant
from somba.db.session import get_db

router = APIRouter(prefix="/v1/invoices", tags=["invoices"])


def _invoice_to_dict(invoice: Invoice) -> dict:
    def _dt(v):
        return v.isoformat() if v else None

    return {
        "id": invoice.id,
        "subscription_id": invoice.subscription_id,
        "customer_id": invoice.customer_id,
        "amount": invoice.amount,
        "status": invoice.status.value,
        "type": invoice.type.value,
        "period_start": _dt(invoice.period_start),
        "period_end": _dt(invoice.period_end),
        "due_date": _dt(invoice.due_date),
        "paid_at": _dt(invoice.paid_at),
    }


def _line_item_to_dict(li: InvoiceLineItem) -> dict:
    def _dt(v):
        return v.isoformat() if v else None

    return {
        "id": li.id,
        "type": li.type.value,
        "description": li.description,
        "amount": li.amount,
        "period_start": _dt(li.period_start),
        "period_end": _dt(li.period_end),
    }


@router.get("")
def list_invoices(
    subscription_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    stmt = select(Invoice).where(Invoice.merchant_id == merchant.id).order_by(Invoice.id.desc())
    if subscription_id is not None:
        stmt = stmt.where(Invoice.subscription_id == subscription_id)
    invoices = list(db.scalars(stmt))
    return {"invoices": [_invoice_to_dict(i) for i in invoices]}


@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    invoice = db.scalar(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.merchant_id == merchant.id)
    )
    if invoice is None:
        raise APIError(code="not_found", message="Invoice not found", status_code=404)

    line_items = list(
        db.scalars(select(InvoiceLineItem).where(InvoiceLineItem.invoice_id == invoice_id))
    )

    return {
        "invoice": {
            **_invoice_to_dict(invoice),
            "line_items": [_line_item_to_dict(li) for li in line_items],
        }
    }
