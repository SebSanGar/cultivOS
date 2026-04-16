"""Intervention scoring endpoint — ranks treatments by predicted impact."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm, FarmerFeedback, Field, TreatmentRecord
from cultivos.db.session import get_db
from cultivos.models.intervention_score import InterventionScoreOut
from cultivos.services.intelligence.intervention_score import (
    FeedbackSummary,
    score_treatments,
)

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["intervention-scores"],
    dependencies=[Depends(get_current_user)]
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("/intervention-scores", response_model=list[InterventionScoreOut])
def get_intervention_scores(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Score and rank existing treatment recommendations by predicted impact.

    Uses farmer feedback data (when available) to boost success probability
    of treatments with proven track records. Returns treatments sorted by
    composite intervention score (highest first).
    """
    field = _get_field(farm_id, field_id, db)

    # Fetch latest treatments for this field (most recent generation)
    treatments = (
        db.query(TreatmentRecord)
        .filter(TreatmentRecord.field_id == field_id)
        .order_by(TreatmentRecord.created_at.desc())
        .all()
    )

    if not treatments:
        return []

    # Build treatment dicts for the pure function
    treatment_dicts = [
        {
            "problema": t.problema,
            "tratamiento": t.tratamiento,
            "costo_estimado_mxn": t.costo_estimado_mxn,
            "urgencia": t.urgencia,
            "health_score_used": t.health_score_used,
            "ancestral_method_name": t.ancestral_method_name,
            "ancestral_base_cientifica": t.ancestral_base_cientifica,
        }
        for t in treatments
    ]

    # Aggregate feedback by problema type across all field feedback
    feedback_rows = (
        db.query(
            TreatmentRecord.problema,
            func.avg(FarmerFeedback.rating).label("avg_rating"),
            func.avg(FarmerFeedback.worked).label("positive_ratio"),
            func.count(FarmerFeedback.id).label("cnt"),
        )
        .join(TreatmentRecord, FarmerFeedback.treatment_id == TreatmentRecord.id)
        .filter(TreatmentRecord.field_id == field_id)
        .group_by(TreatmentRecord.problema)
        .all()
    )

    feedback: dict[str, FeedbackSummary] = {}
    for row in feedback_rows:
        feedback[row.problema] = FeedbackSummary(
            avg_rating=float(row.avg_rating or 0),
            positive_ratio=float(row.positive_ratio or 0),
            count=int(row.cnt or 0),
        )

    hectares = field.hectares or field.computed_area_hectares or 1.0
    return score_treatments(treatment_dicts, feedback=feedback, hectares=hectares)
