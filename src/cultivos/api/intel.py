"""Intelligence dashboard API — cross-farm analytics for admin/research team."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from cultivos.auth import require_role
from cultivos.db.session import get_db
from cultivos.models.intel import (
    AnomaliesOut,
    IntelSummaryOut,
    SoilTrendsOut,
    TreatmentEffectivenessOut,
)
from cultivos.services.intelligence.analytics import (
    compute_anomalies,
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
