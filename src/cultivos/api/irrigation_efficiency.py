"""Farm-level irrigation efficiency aggregate endpoint.

GET /api/farms/{farm_id}/irrigation-efficiency — composes
compute_water_efficiency across every field of the farm, aggregating
efficiency_pct = (1 - water_stress_index) * 100.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, ThermalResult, WeatherRecord
from cultivos.db.session import get_db
from cultivos.models.farm_irrigation_efficiency import (
    FarmIrrigationEfficiencyOut,
    FieldIrrigationItem,
    WorstFieldOut,
)
from cultivos.services.intelligence.water_efficiency import compute_water_efficiency

router = APIRouter(
    prefix="/api/farms/{farm_id}/irrigation-efficiency",
    tags=["water"],
)


def _latest_thermal(db: Session, field_id: int) -> dict | None:
    row = (
        db.query(ThermalResult)
        .filter(ThermalResult.field_id == field_id)
        .order_by(ThermalResult.analyzed_at.desc())
        .first()
    )
    if not row:
        return None
    return {
        "stress_pct": row.stress_pct,
        "irrigation_deficit": row.irrigation_deficit,
    }


def _latest_weather(db: Session, farm_id: int) -> dict | None:
    row = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )
    if not row:
        return None
    return {
        "temp_c": row.temp_c,
        "humidity_pct": row.humidity_pct,
        "recent_rainfall_mm": row.rainfall_mm,
    }


@router.get(
    "",
    response_model=FarmIrrigationEfficiencyOut,
    description=(
        "Aggregate irrigation efficiency across all fields of a farm. "
        "Composes compute_water_efficiency per field and returns avg efficiency, "
        "count of fields below 70%, and the worst-performing field."
    ),
)
def get_farm_irrigation_efficiency(
    farm_id: int,
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    fields = (
        db.query(Field)
        .filter(Field.farm_id == farm_id)
        .order_by(Field.id.asc())
        .all()
    )

    weather_dict = _latest_weather(db, farm_id)

    items: list[FieldIrrigationItem] = []
    for field in fields:
        thermal_dict = _latest_thermal(db, field.id)
        result = compute_water_efficiency(
            hectares=field.hectares or 0.0,
            crop_type=field.crop_type,
            weather=weather_dict,
            thermal=thermal_dict,
        )
        efficiency_pct = round((1.0 - result["water_stress_index"]) * 100.0, 1)
        items.append(
            FieldIrrigationItem(
                field_id=field.id,
                field_name=field.name,
                crop_type=result["crop_type"],
                efficiency_pct=efficiency_pct,
                water_stress_index=result["water_stress_index"],
                optimal_irrigation_mm=result["optimal_irrigation_mm"],
            )
        )

    if items:
        avg_pct = round(sum(i.efficiency_pct for i in items) / len(items), 1)
        fields_below_70 = sum(1 for i in items if i.efficiency_pct < 70.0)
        worst_item = min(items, key=lambda i: (i.efficiency_pct, i.field_id))
        worst = WorstFieldOut(
            field_id=worst_item.field_id,
            field_name=worst_item.field_name,
            crop_type=worst_item.crop_type,
            efficiency_pct=worst_item.efficiency_pct,
            water_stress_index=worst_item.water_stress_index,
        )
    else:
        avg_pct = None
        fields_below_70 = 0
        worst = None

    return FarmIrrigationEfficiencyOut(
        farm_id=farm_id,
        total_fields=len(items),
        avg_water_efficiency_pct=avg_pct,
        fields_below_70pct=fields_below_70,
        worst_field=worst,
        fields=items,
    )
