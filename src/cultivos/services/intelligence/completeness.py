"""Data completeness scoring — checks what data each field has collected."""

from sqlalchemy.orm import Session

from cultivos.db.models import (
    Farm,
    Field,
    NDVIResult,
    SoilAnalysis,
    ThermalResult,
    TreatmentRecord,
    WeatherRecord,
)

DATA_TYPES = 5  # soil, ndvi, thermal, treatments, weather


def compute_data_completeness(db: Session, farm_id: int) -> dict:
    """Compute per-field and farm-aggregate data completeness scores.

    Each field is checked for 5 data types: soil, NDVI, thermal,
    treatments, and weather (farm-level, shared across fields).
    Score = (present types / 5) * 100.
    Farm score = average of field scores (0 if no fields).
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise ValueError(f"Farm {farm_id} not found")

    fields = db.query(Field).filter(Field.farm_id == farm_id).all()
    if not fields:
        return {"farm_id": farm_id, "farm_name": farm.name, "farm_score": 0.0, "fields": []}

    has_weather = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .first()
        is not None
    )

    field_results = []
    for field in fields:
        has_soil = db.query(SoilAnalysis).filter(SoilAnalysis.field_id == field.id).first() is not None
        has_ndvi = db.query(NDVIResult).filter(NDVIResult.field_id == field.id).first() is not None
        has_thermal = db.query(ThermalResult).filter(ThermalResult.field_id == field.id).first() is not None
        has_treatments = db.query(TreatmentRecord).filter(TreatmentRecord.field_id == field.id).first() is not None

        present = sum([has_soil, has_ndvi, has_thermal, has_treatments, has_weather])
        score = round((present / DATA_TYPES) * 100, 1)

        field_results.append({
            "field_id": field.id,
            "field_name": field.name,
            "crop_type": field.crop_type,
            "score": score,
            "has_soil": has_soil,
            "has_ndvi": has_ndvi,
            "has_thermal": has_thermal,
            "has_treatments": has_treatments,
            "has_weather": has_weather,
        })

    farm_score = round(sum(f["score"] for f in field_results) / len(field_results), 1)

    return {
        "farm_id": farm_id,
        "farm_name": farm.name,
        "farm_score": farm_score,
        "fields": field_results,
    }


def compute_global_data_completeness(db: Session, state: str | None = None) -> dict:
    """Aggregate data completeness across ALL farms.

    Returns per-farm summary (score + boolean flags for each data type)
    plus overall stats. Optional state filter.
    """
    query = db.query(Farm)
    if state:
        query = query.filter(Farm.state == state)
    farms = query.all()

    if not farms:
        return {"farms": [], "total_farms": 0, "avg_score": 0.0}

    farm_results = []
    for farm in farms:
        fields = db.query(Field).filter(Field.farm_id == farm.id).all()
        if not fields:
            farm_results.append({
                "farm_id": farm.id,
                "farm_name": farm.name,
                "state": farm.state or "",
                "farm_score": 0.0,
                "field_count": 0,
                "has_soil": False,
                "has_ndvi": False,
                "has_thermal": False,
                "has_treatments": False,
                "has_weather": False,
            })
            continue

        field_ids = [f.id for f in fields]

        has_soil = db.query(SoilAnalysis).filter(SoilAnalysis.field_id.in_(field_ids)).first() is not None
        has_ndvi = db.query(NDVIResult).filter(NDVIResult.field_id.in_(field_ids)).first() is not None
        has_thermal = db.query(ThermalResult).filter(ThermalResult.field_id.in_(field_ids)).first() is not None
        has_treatments = db.query(TreatmentRecord).filter(TreatmentRecord.field_id.in_(field_ids)).first() is not None
        has_weather = db.query(WeatherRecord).filter(WeatherRecord.farm_id == farm.id).first() is not None

        present = sum([has_soil, has_ndvi, has_thermal, has_treatments, has_weather])
        score = round((present / DATA_TYPES) * 100, 1)

        farm_results.append({
            "farm_id": farm.id,
            "farm_name": farm.name,
            "state": farm.state or "",
            "farm_score": score,
            "field_count": len(fields),
            "has_soil": has_soil,
            "has_ndvi": has_ndvi,
            "has_thermal": has_thermal,
            "has_treatments": has_treatments,
            "has_weather": has_weather,
        })

    avg_score = round(sum(f["farm_score"] for f in farm_results) / len(farm_results), 1)

    return {
        "farms": farm_results,
        "total_farms": len(farm_results),
        "avg_score": avg_score,
    }
