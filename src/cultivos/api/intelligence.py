"""Comprehensive field intelligence endpoint — all Cerebro data for a field in one response."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import (
    Farm, Field, HealthScore, NDVIResult, ThermalResult,
    SoilAnalysis, MicrobiomeRecord, WeatherRecord, TreatmentRecord,
)
from cultivos.db.session import get_db
from cultivos.models.intelligence import (
    FieldIntelligenceOut, IntelCarbon, IntelDiseaseRisk, IntelFusion,
    IntelGrowthStage, IntelHealth, IntelMicrobiome, IntelNDVI,
    IntelSoil, IntelThermal, IntelTreatment, IntelWeather, IntelYield,
)
from cultivos.services.crop.disease import assess_disease_weather_risk
from cultivos.services.crop.fusion import validate_sensor_fusion
from cultivos.services.crop.phenology import compute_growth_stage
from cultivos.services.intelligence.carbon import estimate_soc
from cultivos.services.intelligence.yield_model import predict_yield

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["intelligence"],
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("/intelligence", response_model=FieldIntelligenceOut)
def get_field_intelligence(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Return ALL Cerebro intelligence for a single field in one response."""
    field = _get_field(farm_id, field_id, db)

    # --- Fetch latest records from DB ---
    latest_health = (
        db.query(HealthScore).filter(HealthScore.field_id == field.id)
        .order_by(HealthScore.scored_at.desc()).first()
    )
    latest_ndvi = (
        db.query(NDVIResult).filter(NDVIResult.field_id == field.id)
        .order_by(NDVIResult.analyzed_at.desc()).first()
    )
    latest_thermal = (
        db.query(ThermalResult).filter(ThermalResult.field_id == field.id)
        .order_by(ThermalResult.analyzed_at.desc()).first()
    )
    latest_soil = (
        db.query(SoilAnalysis).filter(SoilAnalysis.field_id == field.id)
        .order_by(SoilAnalysis.sampled_at.desc()).first()
    )
    latest_micro = (
        db.query(MicrobiomeRecord).filter(MicrobiomeRecord.field_id == field.id)
        .order_by(MicrobiomeRecord.sampled_at.desc()).first()
    )
    latest_weather = (
        db.query(WeatherRecord).filter(WeatherRecord.farm_id == farm_id)
        .order_by(WeatherRecord.recorded_at.desc()).first()
    )
    treatments = (
        db.query(TreatmentRecord).filter(TreatmentRecord.field_id == field.id)
        .order_by(TreatmentRecord.created_at.desc()).limit(10).all()
    )

    # --- Map DB records to response models ---
    health_out = IntelHealth.model_validate(latest_health) if latest_health else None
    ndvi_out = IntelNDVI.model_validate(latest_ndvi) if latest_ndvi else None
    thermal_out = IntelThermal.model_validate(latest_thermal) if latest_thermal else None
    soil_out = IntelSoil.model_validate(latest_soil) if latest_soil else None
    micro_out = IntelMicrobiome.model_validate(latest_micro) if latest_micro else None
    weather_out = IntelWeather.model_validate(latest_weather) if latest_weather else None
    treatments_out = [IntelTreatment.model_validate(t) for t in treatments]

    # --- Computed: growth stage ---
    growth_out = None
    if field.planted_at:
        gs = compute_growth_stage(field.crop_type or "desconocido", field.planted_at)
        if gs:
            growth_out = IntelGrowthStage(
                stage=gs["stage"],
                stage_es=gs["stage_es"],
                days_since_planting=gs["days_since_planting"],
                days_in_stage=gs["days_in_stage"],
                days_until_next_stage=gs["days_until_next_stage"],
                water_multiplier=gs["water_multiplier"],
                nutrient_focus=gs["nutrient_focus"],
            )

    # --- Computed: disease risk (needs NDVI at minimum) ---
    disease_out = None
    if latest_ndvi:
        dr = assess_disease_weather_risk(
            ndvi_mean=latest_ndvi.ndvi_mean,
            stress_pct=latest_ndvi.stress_pct,
            ndvi_std=latest_ndvi.ndvi_std,
            thermal_stress_pct=latest_thermal.stress_pct if latest_thermal else 0.0,
            thermal_temp_mean=latest_thermal.temp_mean if latest_thermal else 25.0,
            humidity_pct=latest_weather.humidity_pct if latest_weather else 50.0,
            rainfall_mm=latest_weather.rainfall_mm if latest_weather else 0.0,
            temp_c=latest_weather.temp_c if latest_weather else 25.0,
        )
        disease_out = IntelDiseaseRisk(
            risk_level=dr["risk_level"],
            mensaje=dr["mensaje"],
            risks=dr.get("risks", []),
        )

    # --- Computed: yield prediction (needs health or defaults to 50) ---
    yield_out = None
    if field.crop_type and field.hectares:
        health_val = float(latest_health.score) if latest_health else 50.0
        yr = predict_yield(
            crop_type=field.crop_type,
            hectares=field.hectares,
            health_score=health_val,
        )
        yield_out = IntelYield(
            kg_per_ha=yr["kg_per_ha"],
            min_kg_per_ha=yr["min_kg_per_ha"],
            max_kg_per_ha=yr["max_kg_per_ha"],
            total_kg=yr["total_kg"],
            nota=yr["nota"],
        )

    # --- Computed: carbon (needs soil with organic_matter_pct) ---
    carbon_out = None
    if latest_soil and latest_soil.organic_matter_pct is not None:
        soc = estimate_soc(
            organic_matter_pct=float(latest_soil.organic_matter_pct),
            depth_cm=float(latest_soil.depth_cm or 30.0),
        )
        carbon_out = IntelCarbon(
            soc_pct=soc["soc_pct"],
            soc_tonnes_per_ha=soc["soc_tonnes_per_ha"],
            clasificacion=soc["clasificacion"],
            tendencia="datos_insuficientes",  # single point — no trend
        )

    # --- Computed: sensor fusion (needs at least one sensor) ---
    fusion_out = None
    if any([latest_ndvi, latest_thermal, latest_soil, latest_weather]):
        fusion_result = validate_sensor_fusion(
            ndvi={
                "ndvi_mean": latest_ndvi.ndvi_mean,
                "ndvi_std": latest_ndvi.ndvi_std,
                "stress_pct": latest_ndvi.stress_pct,
            } if latest_ndvi else None,
            thermal={
                "stress_pct": latest_thermal.stress_pct,
                "temp_mean": latest_thermal.temp_mean,
                "irrigation_deficit": latest_thermal.irrigation_deficit,
            } if latest_thermal else None,
            soil={
                "ph": latest_soil.ph,
                "organic_matter_pct": latest_soil.organic_matter_pct,
                "nitrogen_ppm": latest_soil.nitrogen_ppm,
                "phosphorus_ppm": latest_soil.phosphorus_ppm,
                "potassium_ppm": latest_soil.potassium_ppm,
                "moisture_pct": latest_soil.moisture_pct,
            } if latest_soil else None,
            weather={
                "temp_c": latest_weather.temp_c,
                "humidity_pct": latest_weather.humidity_pct,
                "wind_kmh": latest_weather.wind_kmh,
            } if latest_weather else None,
        )
        fusion_out = IntelFusion(
            confidence=fusion_result["confidence"],
            contradictions=fusion_result["contradictions"],
            sensors_used=fusion_result["sensors_used"],
            assessment=fusion_result["assessment"],
        )

    return FieldIntelligenceOut(
        field_id=field.id,
        field_name=field.name,
        crop_type=field.crop_type,
        hectares=field.hectares,
        planted_at=field.planted_at,
        health=health_out,
        ndvi=ndvi_out,
        thermal=thermal_out,
        soil=soil_out,
        microbiome=micro_out,
        weather=weather_out,
        growth_stage=growth_out,
        disease_risk=disease_out,
        yield_prediction=yield_out,
        treatments=treatments_out,
        carbon=carbon_out,
        fusion=fusion_out,
    )
