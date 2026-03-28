"""Irrigation optimization endpoints — nested under /api/farms/{farm_id}/fields/{field_id}/irrigation."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, SoilAnalysis, ThermalResult, WeatherRecord
from cultivos.db.session import get_db
from cultivos.models.irrigation import IrrigationScheduleOut
from cultivos.services.intelligence.irrigation import compute_irrigation_schedule

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/irrigation",
    tags=["irrigation"],
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


@router.get("", response_model=IrrigationScheduleOut)
def get_irrigation_schedule(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Compute irrigation schedule based on latest soil, weather, and thermal data."""
    field = _get_field(farm_id, field_id, db)

    # Fetch latest soil analysis for this field
    soil_record = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.field_id == field_id)
        .order_by(SoilAnalysis.sampled_at.desc())
        .first()
    )
    soil_dict = None
    if soil_record:
        soil_dict = {
            "texture": soil_record.texture,
            "moisture_pct": soil_record.moisture_pct,
        }

    # Fetch latest weather for this farm
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

    # Fetch latest thermal result for this field
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

    # Compute growth stage if planted_at is set
    growth_stage = None
    if field.planted_at:
        from cultivos.services.crop.phenology import compute_growth_stage
        stage_result = compute_growth_stage(field.crop_type or "desconocido", field.planted_at)
        if stage_result:
            growth_stage = stage_result["stage"]

    result = compute_irrigation_schedule(
        crop_type=field.crop_type,
        hectares=field.hectares or 0.0,
        soil=soil_dict,
        weather=weather_dict,
        thermal=thermal_dict,
        growth_stage=growth_stage,
    )

    return IrrigationScheduleOut(
        field_id=field_id,
        crop_type=result["crop_type"],
        hectares=result["hectares"],
        schedule=result["schedule"],
        liters_total_per_ha=result["liters_total_per_ha"],
        urgencia=result["urgencia"],
        recomendacion=result["recomendacion"],
    )
