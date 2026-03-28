"""Disease/pest identification endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.models import Disease, Farm, Field, NDVIResult, ThermalResult, WeatherRecord
from cultivos.db.session import get_db
from cultivos.models.disease import DiseaseMatch, DiseaseOut, DiseaseRiskOut, IdentifyRequest
from cultivos.services.crop.disease import assess_disease_weather_risk, identify_diseases

router = APIRouter(
    prefix="/api/knowledge/diseases",
    tags=["diseases"],
)

disease_risk_router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["disease-risk"],
)


@router.get("", response_model=list[DiseaseOut])
def list_diseases(
    crop: str | None = Query(None, description="Filter by affected crop (e.g. maiz, tomate)"),
    db: Session = Depends(get_db),
):
    """List all known diseases/pests, optionally filtered by crop."""
    query = db.query(Disease)
    results = query.all()
    if crop:
        crop_lower = crop.lower()
        results = [d for d in results if crop_lower in [c.lower() for c in (d.affected_crops or [])]]
    return results


@router.post("/identify", response_model=list[DiseaseMatch])
def identify_disease(
    request: IdentifyRequest,
    db: Session = Depends(get_db),
):
    """Identify diseases from reported symptoms. Returns ranked matches with confidence scores."""
    all_diseases = db.query(Disease).all()
    disease_dicts = [
        {
            "id": d.id,
            "name": d.name,
            "description_es": d.description_es,
            "symptoms": d.symptoms or [],
            "affected_crops": d.affected_crops or [],
            "treatments": d.treatments or [],
            "region": d.region,
            "severity": d.severity,
        }
        for d in all_diseases
    ]
    matches = identify_diseases(
        symptoms=request.symptoms,
        diseases=disease_dicts,
        crop=request.crop,
    )
    return matches


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@disease_risk_router.get("/disease-risk", response_model=DiseaseRiskOut)
def get_disease_risk(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Assess disease/pest risk from latest NDVI and thermal data for a field."""
    field = _get_field(farm_id, field_id, db)

    # Fetch latest NDVI result
    ndvi = (
        db.query(NDVIResult)
        .filter(NDVIResult.field_id == field.id)
        .order_by(NDVIResult.id.desc())
        .first()
    )

    # Fetch latest thermal result
    thermal = (
        db.query(ThermalResult)
        .filter(ThermalResult.field_id == field.id)
        .order_by(ThermalResult.id.desc())
        .first()
    )

    # No data — return safe result
    if not ndvi:
        return DiseaseRiskOut(
            field_id=field.id,
            risk_level="sin_riesgo",
            mensaje="Sin riesgo detectado",
            risks=[],
            nota="Sin datos NDVI disponibles para evaluar riesgo",
        )

    # Fetch latest weather record for the farm
    weather = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )

    result = assess_disease_weather_risk(
        ndvi_mean=ndvi.ndvi_mean,
        stress_pct=ndvi.stress_pct,
        ndvi_std=ndvi.ndvi_std,
        thermal_stress_pct=thermal.stress_pct if thermal else 0.0,
        thermal_temp_mean=thermal.temp_mean if thermal else 25.0,
        humidity_pct=weather.humidity_pct if weather else 50.0,
        rainfall_mm=weather.rainfall_mm if weather else 0.0,
        temp_c=weather.temp_c if weather else 25.0,
    )

    return DiseaseRiskOut(
        field_id=field.id,
        risk_level=result["risk_level"],
        mensaje=result["mensaje"],
        risks=result["risks"],
        weather_context=result["weather_context"],
    )
