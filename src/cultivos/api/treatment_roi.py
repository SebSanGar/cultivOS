"""Farm treatment ROI analysis endpoint (#203).

GET /api/farms/{farm_id}/treatment-roi?days=90 — groups TreatmentRecord
entries by tratamiento, computes cost_per_health_point from 30-day
HealthScore followup, returns best/worst ROI treatment types with
Spanish recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm
from cultivos.db.session import get_db
from cultivos.models.treatment_roi import TreatmentROIOut
from cultivos.services.intelligence.treatment_roi import compute_treatment_roi

router = APIRouter(tags=["intelligence"], dependencies=[Depends(get_current_user)])


@router.get(
    "/api/farms/{farm_id}/treatment-roi",
    response_model=TreatmentROIOut,
    description=(
        "Farm treatment ROI analysis — groups TreatmentRecords by tratamiento, "
        "computes cost_per_health_point using 30-day HealthScore followup, "
        "and returns best/worst ROI treatment types. FODECIJAL economic evidence."
    ),
)
def get_treatment_roi(
    farm_id: int,
    days: int = Query(default=90, ge=1, le=365),
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return compute_treatment_roi(farm, db, days=days)
