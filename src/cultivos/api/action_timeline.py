"""Action timeline route — unified 7-day action list for a field.

GET /api/farms/{farm_id}/fields/{field_id}/action-timeline
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, TreatmentRecord, WeatherRecord
from cultivos.db.session import get_db
from cultivos.models.action_timeline import ActionTimelineOut
from cultivos.services.intelligence.action_timeline import build_action_timeline

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["action-timeline"],
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("/action-timeline", response_model=ActionTimelineOut)
def get_action_timeline(
    farm_id: int,
    field_id: int,
    reference_date: Optional[date] = Query(default=None, description="Override date (defaults to today)"),
    db: Session = Depends(get_db),
):
    """Get a unified action timeline for the next 7 days.

    Combines seasonal calendar, growth stage, weather forecast, and
    pending treatments into a single prioritized action list.
    """
    field = _get_field(farm_id, field_id, db)

    # Fetch latest weather record with forecast
    weather = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )
    forecast_3day = []
    if weather and weather.forecast_3day:
        raw = weather.forecast_3day
        forecast_3day = raw if isinstance(raw, list) else []

    # Fetch pending (unapplied) treatments
    pending_rows = (
        db.query(TreatmentRecord)
        .filter(TreatmentRecord.field_id == field_id, TreatmentRecord.applied_at.is_(None))
        .order_by(TreatmentRecord.created_at.desc())
        .all()
    )
    pending_treatments = [
        {
            "id": t.id,
            "problema": t.problema,
            "tratamiento": t.tratamiento,
            "urgencia": t.urgencia,
            "costo_estimado_mxn": t.costo_estimado_mxn,
            "created_at": t.created_at,
        }
        for t in pending_rows
    ]

    result = build_action_timeline(
        reference_date=reference_date,
        crop_type=field.crop_type,
        planted_at=field.planted_at,
        forecast_3day=forecast_3day,
        pending_treatments=pending_treatments,
    )

    return result
