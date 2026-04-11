"""Per-field treatment cost effectiveness endpoint.

GET /api/farms/{farm_id}/fields/{field_id}/treatment-cost-effectiveness
Returns per-treatment cost_mxn and health_delta — FODECIJAL "AI with measurable ROI".
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.intel import TreatmentCostEffectivenessItem
from cultivos.services.intelligence.analytics import compute_field_treatment_cost_effectiveness

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["treatment-effectiveness"],
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("/treatment-cost-effectiveness", response_model=list[TreatmentCostEffectivenessItem])
def get_field_treatment_cost_effectiveness(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Return per-treatment cost_mxn and health_delta for one field.

    health_delta = next HealthScore after treatment application minus health_score_used.
    None when no subsequent health score exists.
    """
    _get_field(farm_id, field_id, db)
    results = compute_field_treatment_cost_effectiveness(field_id, db)
    # Service returns 'delta' key; map to 'health_delta' for the response model
    return [
        TreatmentCostEffectivenessItem(
            tratamiento=r["tratamiento"],
            cost_mxn=r["cost_mxn"],
            health_before=r.get("health_before"),
            health_after=r.get("health_after"),
            health_delta=r.get("health_delta"),
            applied_at=r.get("applied_at"),
        )
        for r in results
    ]
