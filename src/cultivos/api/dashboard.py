"""Dashboard endpoint — aggregates all data for a farm into one response."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult, SoilAnalysis, TreatmentRecord, WeatherRecord
from cultivos.db.session import get_db
from cultivos.models.dashboard import (
    DashboardField,
    DashboardHealthScore,
    DashboardNDVI,
    DashboardOut,
    DashboardSoil,
    DashboardTopRisk,
    DashboardWeather,
)

router = APIRouter(prefix="/api/farms/{farm_id}", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def get_farm_dashboard(farm_id: int, db: Session = Depends(get_db)):
    """Return aggregated dashboard data for a farm: fields with latest scores, weather, overall health."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    fields = db.query(Field).filter(Field.farm_id == farm_id).all()

    dashboard_fields: list[DashboardField] = []
    scores_for_avg: list[float] = []

    for field in fields:
        # Latest health score
        latest_hs = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == field.id)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )

        # Latest NDVI
        latest_ndvi = (
            db.query(NDVIResult)
            .filter(NDVIResult.field_id == field.id)
            .order_by(NDVIResult.analyzed_at.desc())
            .first()
        )

        # Latest soil
        latest_soil = (
            db.query(SoilAnalysis)
            .filter(SoilAnalysis.field_id == field.id)
            .order_by(SoilAnalysis.sampled_at.desc())
            .first()
        )

        hs_out = DashboardHealthScore.model_validate(latest_hs) if latest_hs else None
        ndvi_out = DashboardNDVI.model_validate(latest_ndvi) if latest_ndvi else None
        soil_out = DashboardSoil.model_validate(latest_soil) if latest_soil else None

        if latest_hs:
            scores_for_avg.append(latest_hs.score)

        dashboard_fields.append(DashboardField(
            id=field.id,
            name=field.name,
            crop_type=field.crop_type,
            hectares=field.hectares,
            latest_health_score=hs_out,
            latest_ndvi=ndvi_out,
            latest_soil=soil_out,
        ))

    # Sort by urgency: fields with health scores sorted ascending (lowest/worst first),
    # fields without scores go to the end
    dashboard_fields.sort(
        key=lambda f: (
            0 if f.latest_health_score else 1,
            f.latest_health_score.score if f.latest_health_score else 999,
        )
    )

    # Overall health: average of all field scores, or None if no scores
    overall_health = round(sum(scores_for_avg) / len(scores_for_avg), 1) if scores_for_avg else None

    # Latest weather for this farm
    latest_weather = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )
    weather_out = DashboardWeather.model_validate(latest_weather) if latest_weather else None

    # Treatment count across all fields
    field_ids = [f.id for f in fields]
    treatment_count = 0
    if field_ids:
        treatment_count = (
            db.query(TreatmentRecord)
            .filter(TreatmentRecord.field_id.in_(field_ids))
            .count()
        )

    # Top risk: field with lowest health score
    top_risk = None
    if dashboard_fields and dashboard_fields[0].latest_health_score:
        worst = dashboard_fields[0]  # already sorted ascending by score
        top_risk = DashboardTopRisk(
            field_name=worst.name,
            score=worst.latest_health_score.score,
            trend=worst.latest_health_score.trend,
        )

    return DashboardOut(
        farm=farm,
        fields=dashboard_fields,
        overall_health=overall_health,
        weather=weather_out,
        treatment_count=treatment_count,
        top_risk=top_risk,
    )
