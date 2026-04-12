"""Field intervention effectiveness endpoint (#206).

GET /api/farms/{farm_id}/fields/{field_id}/intervention-effectiveness?days=180
— per-treatment-name effectiveness, classifying TreatmentRecord deltas as
effective / neutral / counterproductive using ±3d baseline + 30d followup
HealthScore lookups. Returns best/worst treatment + Spanish recommendation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.field_intervention_effectiveness import (
    FieldInterventionEffectivenessOut,
)
from cultivos.services.intelligence.field_intervention_effectiveness import (
    compute_field_intervention_effectiveness,
)

router = APIRouter(tags=["intelligence"])


@router.get(
    "/api/farms/{farm_id}/fields/{field_id}/intervention-effectiveness",
    response_model=FieldInterventionEffectivenessOut,
    description=(
        "Per-field intervention effectiveness — classifies each TreatmentRecord "
        "as effective/neutral/counterproductive using ±3d baseline + 30d followup "
        "HealthScore lookups. Returns best/worst treatment by avg delta. "
        "FODECIJAL evidence per field."
    ),
)
def get_field_intervention_effectiveness(
    farm_id: int,
    field_id: int,
    days: int = Query(default=180, ge=1, le=365),
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
    return compute_field_intervention_effectiveness(field, db, days=days)
