"""Farmer feedback endpoints — rate treatments and suggest traditional alternatives."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, FarmerFeedback, Field, TreatmentRecord
from cultivos.db.session import get_db
from cultivos.models.feedback import FeedbackIn, FeedbackOut

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/feedback",
    tags=["feedback"],
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


@router.post("", response_model=FeedbackOut, status_code=201)
def submit_feedback(
    farm_id: int,
    field_id: int,
    payload: FeedbackIn,
    db: Session = Depends(get_db),
):
    """Submit farmer feedback on a treatment recommendation."""
    field = _get_field(farm_id, field_id, db)

    # Verify treatment exists and belongs to this field
    treatment = db.query(TreatmentRecord).filter(
        TreatmentRecord.id == payload.treatment_id,
        TreatmentRecord.field_id == field_id,
    ).first()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found for this field")

    record = FarmerFeedback(
        field_id=field_id,
        treatment_id=payload.treatment_id,
        rating=payload.rating,
        worked=payload.worked,
        farmer_notes=payload.farmer_notes,
        alternative_method=payload.alternative_method,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[FeedbackOut])
def list_feedback(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """List all farmer feedback for this field, most recent first."""
    _get_field(farm_id, field_id, db)
    return (
        db.query(FarmerFeedback)
        .filter(FarmerFeedback.field_id == field_id)
        .order_by(FarmerFeedback.created_at.desc())
        .all()
    )
