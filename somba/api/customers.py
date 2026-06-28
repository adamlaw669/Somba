"""Customers CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.api.errors import APIError
from somba.api.middleware.auth import get_current_merchant
from somba.db.models import Customer, Merchant
from somba.db.session import get_db

router = APIRouter(prefix="/v1/customers", tags=["customers"])


def _customer_to_dict(c: Customer) -> dict:
    return {
        "id": c.id,
        "merchant_id": c.merchant_id,
        "external_id": c.external_id,
        "email": c.email,
        "name": c.name,
        "va_account_no": c.va_account_no,
        "credit_balance": c.credit_balance,
    }


def _get_customer_or_404(db: Session, customer_id: int, merchant: Merchant) -> Customer:
    customer = db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.merchant_id == merchant.id,
        )
    )
    if customer is None:
        raise APIError(code="not_found", message="Customer not found", status_code=404)
    return customer


class CustomerCreateRequest(BaseModel):
    external_id: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    name: str | None = Field(default=None, max_length=255)


class CustomerUpdateRequest(BaseModel):
    external_id: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    name: str | None = Field(default=None, max_length=255)


@router.post("", status_code=201)
def create_customer(
    body: CustomerCreateRequest,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    customer = Customer(
        merchant_id=merchant.id,
        external_id=body.external_id,
        email=body.email,
        name=body.name,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return {"customer": _customer_to_dict(customer)}


@router.get("")
def list_customers(
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    customers = list(
        db.scalars(select(Customer).where(Customer.merchant_id == merchant.id))
    )
    return {"customers": [_customer_to_dict(c) for c in customers]}


@router.get("/{customer_id}")
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    return {"customer": _customer_to_dict(_get_customer_or_404(db, customer_id, merchant))}


@router.patch("/{customer_id}")
def update_customer(
    customer_id: int,
    body: CustomerUpdateRequest,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    customer = _get_customer_or_404(db, customer_id, merchant)
    if body.external_id is not None:
        customer.external_id = body.external_id
    if body.email is not None:
        customer.email = body.email
    if body.name is not None:
        customer.name = body.name
    db.commit()
    db.refresh(customer)
    return {"customer": _customer_to_dict(customer)}


@router.delete("/{customer_id}", status_code=200)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    customer = _get_customer_or_404(db, customer_id, merchant)
    db.delete(customer)
    db.commit()
    return {"deleted": True, "id": customer_id}
