"""Cumulative savings + breakeven endpoint for owner economic-impact view.

GET /api/farms/{farm_id}/cumulative-savings — returns monthly cumulative
savings from treatment history and the breakeven month (when cumulative
savings >= annual subscription cost).
"""

from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, TreatmentRecord
from cultivos.db.session import get_db
from cultivos.models.cumulative_savings import CumulativeSavingsOut, CumulativeSavingsPoint
from cultivos.services.intelligence.assumptions import get_value as _a

router = APIRouter(tags=["economics"])

_TIER_RATES = {
    "basic": _a("tier_rate_basic_mxn_ha"),
    "standard": _a("tier_rate_standard_mxn_ha"),
}
_SAVINGS_PER_TREATMENT = _a("per_treatment_savings_mxn")


@router.get(
    "/api/farms/{farm_id}/cumulative-savings",
    response_model=CumulativeSavingsOut,
)
def get_cumulative_savings(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Monthly cumulative savings from treatment history + breakeven marker."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    field_ids = [
        r.id for r in db.query(Field.id).filter(Field.farm_id == farm_id).all()
    ]

    if not field_ids:
        return CumulativeSavingsOut(farm_id=farm_id, data_points=[])

    treatments = (
        db.query(TreatmentRecord)
        .filter(TreatmentRecord.field_id.in_(field_ids))
        .order_by(TreatmentRecord.created_at)
        .all()
    )

    if not treatments:
        return CumulativeSavingsOut(farm_id=farm_id, data_points=[])

    # Bucket treatments by (year, month)
    monthly_savings: dict[tuple, int] = defaultdict(int)
    for tr in treatments:
        created = tr.created_at or datetime.utcnow()
        key = (created.year, created.month)
        monthly_savings[key] += round(_SAVINGS_PER_TREATMENT)

    # Sort months chronologically, produce cumulative series (month=1,2,3...)
    sorted_months = sorted(monthly_savings.keys())
    cumulative = 0
    data_points = []
    for idx, key in enumerate(sorted_months, start=1):
        cumulative += monthly_savings[key]
        data_points.append(
            CumulativeSavingsPoint(month=idx, cumulative_savings_mxn=cumulative)
        )

    # Subscription cost
    tier = getattr(farm, "tier", None)
    total_hectares = getattr(farm, "total_hectares", None) or 0.0
    subscription_cost_mxn: int | None = None
    if tier and tier in _TIER_RATES and total_hectares > 0:
        subscription_cost_mxn = round(total_hectares * _TIER_RATES[tier])

    # Breakeven = first month where cumulative >= subscription_cost
    breakeven_month: int | None = None
    if subscription_cost_mxn is not None:
        for pt in data_points:
            if pt.cumulative_savings_mxn >= subscription_cost_mxn:
                breakeven_month = pt.month
                break

    return CumulativeSavingsOut(
        farm_id=farm_id,
        data_points=data_points,
        breakeven_month=breakeven_month,
        subscription_cost_mxn=subscription_cost_mxn,
    )
