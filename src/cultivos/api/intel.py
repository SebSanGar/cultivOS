"""Intelligence dashboard API — cross-farm analytics for admin/research team."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import require_role
from cultivos.db.models import Farm, FarmerFeedback, Field, TreatmentRecord
from cultivos.db.session import get_db
from cultivos.models.feedback import TEKMethodValidation, TEKValidationOut
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


@router.get("/tek-validation", response_model=TEKValidationOut)
def tek_validation(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Aggregate farmer feedback by ancestral method to see which TEK methods farmers trust."""
    # Get all feedback joined with treatments that have an ancestral method
    results = (
        db.query(FarmerFeedback, TreatmentRecord)
        .join(TreatmentRecord, FarmerFeedback.treatment_id == TreatmentRecord.id)
        .filter(TreatmentRecord.ancestral_method_name.isnot(None))
        .all()
    )

    # Aggregate by method name
    method_data: dict[str, list[FarmerFeedback]] = {}
    for feedback, treatment in results:
        name = treatment.ancestral_method_name
        method_data.setdefault(name, []).append(feedback)

    methods = []
    for method_name, feedbacks in method_data.items():
        total = len(feedbacks)
        positive = sum(1 for f in feedbacks if f.worked)
        negative = total - positive
        avg_rating = sum(f.rating for f in feedbacks) / total
        # Trust score: weighted combination of positive ratio (60%) and normalized rating (40%)
        positive_ratio = positive / total if total > 0 else 0
        rating_normalized = (avg_rating - 1) / 4  # 1-5 → 0-1
        trust_score = round((positive_ratio * 0.6 + rating_normalized * 0.4) * 100, 1)

        methods.append(TEKMethodValidation(
            method_name=method_name,
            total_feedback=total,
            positive_count=positive,
            negative_count=negative,
            average_rating=round(avg_rating, 2),
            trust_score=trust_score,
        ))

    # Sort by trust score descending
    methods.sort(key=lambda m: m.trust_score, reverse=True)
    return TEKValidationOut(methods=methods)


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
