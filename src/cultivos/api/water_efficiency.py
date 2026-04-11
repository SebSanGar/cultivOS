"""Water use efficiency report endpoint.

GET /api/farms/{farm_id}/fields/{field_id}/water-efficiency
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, ThermalResult, WeatherRecord
from cultivos.db.session import get_db
from cultivos.models.water_efficiency import WaterEfficiencyOut
from cultivos.services.intelligence.water_efficiency import compute_water_efficiency

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/water-efficiency",
    tags=["water"],
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("", response_model=WaterEfficiencyOut)
def get_water_efficiency(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Compute water use efficiency for a field using latest thermal and weather data."""
    field = _get_field(farm_id, field_id, db)

    thermal_record = (
        db.query(ThermalResult)
        .filter(ThermalResult.field_id == field_id)
        .order_by(ThermalResult.analyzed_at.desc())
        .first()
    )
    thermal_dict = None
    if thermal_record:
        thermal_dict = {
            "stress_pct": thermal_record.stress_pct,
            "irrigation_deficit": thermal_record.irrigation_deficit,
        }

    weather_record = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )
    weather_dict = None
    if weather_record:
        weather_dict = {
            "temp_c": weather_record.temp_c,
            "humidity_pct": weather_record.humidity_pct,
            "recent_rainfall_mm": weather_record.rainfall_mm,
        }

    result = compute_water_efficiency(
        hectares=field.hectares or 0.0,
        crop_type=field.crop_type,
        weather=weather_dict,
        thermal=thermal_dict,
    )

    return WaterEfficiencyOut(
        field_id=field_id,
        **result,
    )
