"""Farm-level region-aware recommendations — GET /api/farms/{farm_id}/recommendations.

Resolves the farm's region from its state/country, fetches latest health + soil
for each field, runs the recommendation engine with region context, and returns
aggregated results with the region profile.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import (
    AncestralMethod,
    Farm,
    Field,
    HealthScore,
    MicrobiomeRecord,
    SoilAnalysis,
    WeatherRecord,
)
from cultivos.db.session import get_db
from cultivos.services.intelligence.recommendations import (
    AncestralMethodData,
    ForecastInput,
    MicrobiomeInput,
    RegionInput,
    SoilInput,
    WeatherInput,
    recommend_treatment,
)
from cultivos.services.intelligence.regions import get_region_profile

router = APIRouter(
    prefix="/api/farms/{farm_id}/recommendations",
    tags=["recommendations"],
    dependencies=[Depends(get_current_user)]
)


class RegionOut(BaseModel):
    region_name: str
    climate_zone: str
    soil_type: str
    growing_season: str
    key_crops: list[str]
    currency: str
    seasonal_notes: str


class RecommendationItem(BaseModel):
    field_id: int
    field_name: str
    crop_type: str | None = None
    health_score: float
    problema: str
    causa_probable: str
    tratamiento: str
    costo_estimado_mxn: int
    costo_estimado_cad: float | None = None
    urgencia: str
    prevencion: str
    organic: bool = True
    metodo_ancestral: str | None = None
    base_cientifica: str | None = None
    razon_match: str | None = None
    timing_consejo: str | None = None
    contexto_regional: str | None = None


class FarmRecommendationsOut(BaseModel):
    farm_id: int
    farm_name: str
    region: RegionOut
    generated_at: str
    recommendations: list[RecommendationItem]


@router.get("", response_model=FarmRecommendationsOut)
def farm_recommendations(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Generate region-calibrated recommendations for all fields in a farm.

    Resolves the farm's agricultural region from its state/country,
    then runs the recommendation engine per field with region context injected.
    Returns 404 if farm not found, 422 if no fields have health scores.
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    # Resolve region profile
    region_profile = get_region_profile(
        state=farm.state or "Jalisco",
        country=farm.country or "MX",
    )
    region_input = RegionInput(**region_profile)

    fields = db.query(Field).filter(Field.farm_id == farm_id).all()
    if not fields:
        raise HTTPException(status_code=422, detail="Farm has no fields")

    # Fetch ancestral methods once (shared across fields)
    ancestral_rows = db.query(AncestralMethod).all()
    ancestral_data: list[AncestralMethodData] = [
        AncestralMethodData(
            name=m.name,
            practice_type=m.practice_type,
            crops=m.crops or [],
            benefits_es=m.benefits_es,
            scientific_basis=m.scientific_basis or "",
        )
        for m in ancestral_rows
    ]

    # Fetch latest weather for farm (shared across fields)
    latest_weather = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )
    weather_input: WeatherInput | None = None
    if latest_weather:
        forecast_data = latest_weather.forecast_3day or []
        weather_input = WeatherInput(
            temp_c=latest_weather.temp_c,
            humidity_pct=latest_weather.humidity_pct,
            wind_kmh=latest_weather.wind_kmh,
            description=latest_weather.description,
            forecast_3day=[
                ForecastInput(
                    temp_c=f.get("temp_c", 0),
                    humidity_pct=f.get("humidity_pct", 0),
                    wind_kmh=f.get("wind_kmh", 0),
                    description=f.get("description", ""),
                )
                for f in forecast_data
            ],
        )

    all_recs: list[RecommendationItem] = []
    fields_with_scores = 0

    for field in fields:
        latest_health = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == field.id)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )
        if not latest_health:
            continue

        fields_with_scores += 1

        # Fetch latest soil
        latest_soil = (
            db.query(SoilAnalysis)
            .filter(SoilAnalysis.field_id == field.id)
            .order_by(SoilAnalysis.sampled_at.desc())
            .first()
        )
        soil_input: SoilInput | None = None
        if latest_soil:
            soil_input = SoilInput(
                ph=latest_soil.ph,
                organic_matter_pct=latest_soil.organic_matter_pct,
                nitrogen_ppm=latest_soil.nitrogen_ppm,
                phosphorus_ppm=latest_soil.phosphorus_ppm,
                potassium_ppm=latest_soil.potassium_ppm,
                moisture_pct=latest_soil.moisture_pct,
            )

        # Fetch latest microbiome
        latest_micro = (
            db.query(MicrobiomeRecord)
            .filter(MicrobiomeRecord.field_id == field.id)
            .order_by(MicrobiomeRecord.sampled_at.desc())
            .first()
        )
        micro_input: MicrobiomeInput | None = None
        if latest_micro:
            micro_input = MicrobiomeInput(
                respiration_rate=latest_micro.respiration_rate,
                microbial_biomass_carbon=latest_micro.microbial_biomass_carbon,
                fungi_bacteria_ratio=latest_micro.fungi_bacteria_ratio,
                classification=latest_micro.classification,
            )

        # Compute growth stage
        growth_stage = None
        if field.planted_at:
            from cultivos.services.crop.phenology import compute_growth_stage
            stage_result = compute_growth_stage(field.crop_type or "desconocido", field.planted_at)
            if stage_result:
                growth_stage = stage_result["stage"]

        recs = recommend_treatment(
            health_score=latest_health.score,
            soil=soil_input,
            crop_type=field.crop_type,
            microbiome=micro_input,
            ancestral_methods=ancestral_data,
            weather=weather_input,
            growth_stage=growth_stage,
            region=region_input,
        )

        for rec in recs:
            all_recs.append(RecommendationItem(
                field_id=field.id,
                field_name=field.name,
                crop_type=field.crop_type,
                health_score=latest_health.score,
                problema=rec["problema"],
                causa_probable=rec["causa_probable"],
                tratamiento=rec["tratamiento"],
                costo_estimado_mxn=rec["costo_estimado_mxn"],
                costo_estimado_cad=rec.get("costo_estimado_cad"),
                urgencia=rec["urgencia"],
                prevencion=rec["prevencion"],
                organic=rec.get("organic", True),
                metodo_ancestral=rec.get("metodo_ancestral"),
                base_cientifica=rec.get("base_cientifica"),
                razon_match=rec.get("razon_match"),
                timing_consejo=rec.get("timing_consejo"),
                contexto_regional=rec.get("contexto_regional"),
            ))

    if fields_with_scores == 0:
        raise HTTPException(
            status_code=422,
            detail="No fields have health scores. Compute health scores first.",
        )

    return FarmRecommendationsOut(
        farm_id=farm.id,
        farm_name=farm.name,
        region=RegionOut(**region_profile),
        generated_at=datetime.utcnow().isoformat(),
        recommendations=all_recs,
    )
