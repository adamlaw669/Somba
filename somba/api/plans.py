"""Plans CRUD endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from somba.api.errors import APIError
from somba.api.middleware.auth import get_current_merchant
from somba.db.models import Merchant, Plan, PlanStatus
from somba.db.session import get_db

router = APIRouter(prefix="/v1/plans", tags=["plans"])


def _plan_to_dict(plan: Plan) -> dict:
    return {
        "id": plan.id,
        "merchant_id": plan.merchant_id,
        "name": plan.name,
        "amount": plan.amount,
        "currency": plan.currency,
        "interval": plan.interval,
        "interval_count": plan.interval_count,
        "trial_days": plan.trial_days,
        "status": plan.status.value,
    }


def _get_plan_or_404(db: Session, plan_id: int, merchant: Merchant) -> Plan:
    plan = db.scalar(
        select(Plan).where(Plan.id == plan_id, Plan.merchant_id == merchant.id)
    )
    if plan is None:
        raise APIError(code="not_found", message="Plan not found", status_code=404)
    return plan


class PlanCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    amount: int = Field(gt=0, description="Amount in smallest currency unit (e.g. kobo)")
    currency: str = Field(default="NGN", min_length=3, max_length=3)
    interval: Literal["day", "week", "month", "year"]
    interval_count: int = Field(default=1, ge=1)
    trial_days: int = Field(default=0, ge=0)


class PlanUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    trial_days: int | None = Field(default=None, ge=0)
    status: Literal["active", "archived"] | None = None


@router.post("", status_code=201)
def create_plan(
    body: PlanCreateRequest,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    plan = Plan(
        merchant_id=merchant.id,
        name=body.name,
        amount=body.amount,
        currency=body.currency.upper(),
        interval=body.interval,
        interval_count=body.interval_count,
        trial_days=body.trial_days,
        status=PlanStatus.active,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return {"plan": _plan_to_dict(plan)}


@router.get("")
def list_plans(
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    plans = list(db.scalars(select(Plan).where(Plan.merchant_id == merchant.id)))
    return {"plans": [_plan_to_dict(p) for p in plans]}


@router.get("/{plan_id}")
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    return {"plan": _plan_to_dict(_get_plan_or_404(db, plan_id, merchant))}


@router.patch("/{plan_id}")
def update_plan(
    plan_id: int,
    body: PlanUpdateRequest,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    plan = _get_plan_or_404(db, plan_id, merchant)
    if body.name is not None:
        plan.name = body.name
    if body.trial_days is not None:
        plan.trial_days = body.trial_days
    if body.status is not None:
        plan.status = PlanStatus(body.status)
    db.commit()
    db.refresh(plan)
    return {"plan": _plan_to_dict(plan)}


@router.delete("/{plan_id}", status_code=200)
def archive_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> dict:
    plan = _get_plan_or_404(db, plan_id, merchant)
    if plan.status == PlanStatus.archived:
        raise APIError(code="already_archived", message="Plan is already archived", status_code=400)
    plan.status = PlanStatus.archived
    db.commit()
    return {"plan": _plan_to_dict(plan)}
