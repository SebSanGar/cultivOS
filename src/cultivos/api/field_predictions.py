"""Per-field prediction accuracy endpoint.

Surfaces PredictionSnapshot accuracy metrics scoped to a single field so
the frontend can show per-field AI validation — complements the global
endpoint at /api/intel/prediction-accuracy.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.intel import FieldPredictionAccuracyOut
from cultivos.services.intelligence.analytics import compute_field_prediction_accuracy

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/predictions",
    tags=["predictions"],
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("/accuracy", response_model=FieldPredictionAccuracyOut)
def get_field_prediction_accuracy(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Return MAPE, resolved/pending counts, and per-type breakdown for one field."""
    _get_field(farm_id, field_id, db)
    result = compute_field_prediction_accuracy(db, field_id)
    return FieldPredictionAccuracyOut(**result)
