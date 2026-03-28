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
