"""Field risk heatmap endpoint — GET /api/farms/{farm_id}/fields/risk-map."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.session import get_db
from cultivos.models.risk_map import FieldRiskItem
from cultivos.services.intelligence.risk_map import compute_farm_risk_map

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields",
    tags=["risk-map"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/risk-map", response_model=list[FieldRiskItem])
def get_farm_risk_map(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Return a risk score for every field in a farm.

    risk_score: 0-100 (higher = more at risk). Combines:
    - Latest health score (inverted, 40% weight)
    - Disease/pest risk from NDVI + weather (25%)
    - Weather alert severity (20%)
    - Thermal stress (15%)

    Fields with no data return null risk_score and null dominant_factor.
    """
    try:
        return compute_farm_risk_map(farm_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
