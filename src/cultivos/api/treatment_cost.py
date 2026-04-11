"""Per-field treatment cost effectiveness endpoint — task #125."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.services.intelligence.analytics import compute_field_treatment_cost_effectiveness

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["treatments"],
)


class TreatmentCostItem(BaseModel):
    tratamiento: str
    cost_mxn: int
    health_before: float
    health_after: float | None = None
    health_delta: float | None = None
    applied_at: str | None = None


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("/treatment-cost-effectiveness", response_model=list[TreatmentCostItem])
def get_treatment_cost_effectiveness(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Return per-treatment cost and health delta for a single field."""
    _get_field(farm_id, field_id, db)
    return compute_field_treatment_cost_effectiveness(field_id, db)
