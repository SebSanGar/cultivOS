"""Field NDVI-health correlation endpoint (#212).

GET /api/farms/{farm_id}/fields/{field_id}/ndvi-health-correlation?days=90
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.ndvi_health_correlation import NdviHealthCorrelationOut
from cultivos.services.intelligence.ndvi_health_correlation import (
    compute_ndvi_health_correlation,
)

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/ndvi-health-correlation",
    tags=["intelligence"],
    dependencies=[Depends(get_current_user)]
)


@router.get(
    "",
    response_model=NdviHealthCorrelationOut,
    description=(
        "Pearson correlation between HealthScore.ndvi_mean and "
        "HealthScore.score over the last N days. Strength tiers: strong "
        "(|r|>=0.7), moderate (0.4-0.7), weak (0.15-0.4), none (<0.15). "
        "Fewer than 5 valid samples → insufficient_data."
    ),
)
def get_ndvi_health_correlation(
    farm_id: int,
    field_id: int,
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = (
        db.query(Field)
        .filter(Field.id == field_id, Field.farm_id == farm_id)
        .first()
    )
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    result = compute_ndvi_health_correlation(
        field_id=field_id, period_days=days, db=db
    )
    return NdviHealthCorrelationOut(field_id=field_id, **result)
