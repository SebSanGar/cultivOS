"""Intelligence dashboard API — cross-farm analytics for admin/research team."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import require_role
from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.intel import (
    AnomaliesOut,
    IntelSummaryOut,
    SeasonalOut,
    SoilTrendsOut,
    TreatmentEffectivenessOut,
)
from cultivos.services.intelligence.analytics import (
    compute_anomalies,
    compute_seasonal_performance,
    compute_soil_trends,
    compute_summary,
    compute_treatment_effectiveness,
)

router = APIRouter(prefix="/api/intel", tags=["intelligence"])

_admin_or_researcher = require_role("admin", "researcher")


@router.get("/summary", response_model=IntelSummaryOut)
def intel_summary(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    return compute_summary(db)


@router.get("/soil-trends", response_model=SoilTrendsOut)
def intel_soil_trends(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    return compute_soil_trends(db)


@router.get("/treatments", response_model=TreatmentEffectivenessOut)
def intel_treatments(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    return compute_treatment_effectiveness(db)


@router.get("/anomalies", response_model=AnomaliesOut)
def intel_anomalies(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    return compute_anomalies(db)


seasonal_router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["intelligence"],
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    """Validate farm and field exist and are linked."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@seasonal_router.get("/seasonal", response_model=SeasonalOut)
def field_seasonal(
    farm_id: int,
    field_id: int,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    field = _get_field(farm_id, field_id, db)
    return compute_seasonal_performance(db, field.id, year=year)
