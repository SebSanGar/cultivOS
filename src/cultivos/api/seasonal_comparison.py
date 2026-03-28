"""Seasonal comparison endpoint — temporal vs secas side-by-side metrics."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
from cultivos.db.session import get_db
from cultivos.services.intelligence.seasonal_comparison import compute_seasonal_comparison

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/seasonal-comparison",
    tags=["seasonal-comparison"],
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("")
def get_seasonal_comparison(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    field = _get_field(farm_id, field_id, db)

    health_rows = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field.id)
        .order_by(HealthScore.scored_at.desc())
        .all()
    )
    treatment_rows = (
        db.query(TreatmentRecord)
        .filter(TreatmentRecord.field_id == field.id)
        .all()
    )

    health_records = [
        {"score": h.score, "ndvi_mean": h.ndvi_mean, "scored_at": h.scored_at}
        for h in health_rows
        if h.scored_at is not None
    ]
    treatments = [
        {"created_at": t.created_at}
        for t in treatment_rows
        if t.created_at is not None
    ]

    return compute_seasonal_comparison(health_records, treatments)
