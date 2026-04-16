"""Yield prediction endpoints — nested under /api/farms/{farm_id}/fields/{field_id}/yield."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm, Field, HealthScore
from cultivos.db.session import get_db
from cultivos.models.yield_pred import YieldPredictionOut
from cultivos.services.intelligence.yield_model import predict_yield

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/yield",
    tags=["yield"],
    dependencies=[Depends(get_current_user)]
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    """Validate farm and field exist."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("", response_model=YieldPredictionOut)
def get_yield_prediction(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Predict yield based on latest health score, crop type, and field area."""
    field = _get_field(farm_id, field_id, db)

    # Fetch latest health score for this field
    health_record = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field_id)
        .order_by(HealthScore.scored_at.desc())
        .first()
    )

    health_score = 50.0  # default when no health data
    if health_record:
        health_score = float(health_record.score)

    result = predict_yield(
        crop_type=field.crop_type or "desconocido",
        hectares=field.hectares or 0.0,
        health_score=health_score,
    )

    nota = result["nota"]
    if not health_record:
        nota = "Datos de salud insuficientes — prediccion basada en promedio. " + nota

    return YieldPredictionOut(
        field_id=field_id,
        crop_type=result["crop_type"],
        hectares=result["hectares"],
        kg_per_ha=result["kg_per_ha"],
        min_kg_per_ha=result["min_kg_per_ha"],
        max_kg_per_ha=result["max_kg_per_ha"],
        total_kg=result["total_kg"],
        nota=nota,
    )
