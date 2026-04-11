"""Farm and Field CRUD endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user, require_role
from cultivos.db.models import Farm, Field, User
from cultivos.db.session import get_db
from cultivos.models.farm import (
    FarmCreate, FarmUpdate, FarmOut,
    FieldCreate, FieldUpdate, FieldOut,
    HeatmapResponse, FieldHeatmapPoint,
)
from cultivos.models.daily_briefing import DailyBriefingOut
from cultivos.models.disease_risk_assessment import DiseaseRiskAssessmentOut
from cultivos.models.field_priority import FieldPriorityOut
from cultivos.models.growth_report import GrowthReportOut
from cultivos.models.intel import FarmExecutiveSummaryOut
from cultivos.models.stress_report import FieldStressReportOut
from cultivos.models.upcoming_treatments import UpcomingTreatmentOut
from cultivos.models.carbon_baseline import CarbonBaselineIn, CarbonBaselineOut, CarbonProjectionOut
from cultivos.models.forecast_alerts import ForecastAlertsOut
from cultivos.models.field_timeline import FieldTimelineOut
from cultivos.models.progress_report import ProgressReportOut
from cultivos.models.regen_trajectory import RegenTrajectoryOut
from cultivos.models.water_stress import WaterStressOut
from cultivos.models.yield_forecast import FarmYieldForecastOut
from cultivos.services.intelligence.analytics import compute_farm_executive_summary
from cultivos.services.intelligence.daily_briefing import compute_daily_briefing
from cultivos.services.intelligence.disease_risk_assessment import compute_disease_risk_assessment
from cultivos.services.intelligence.field_priority import compute_field_priority
from cultivos.services.intelligence.forecast_alerts import compute_forecast_alerts
from cultivos.services.intelligence.growth_report import compute_growth_report
from cultivos.services.intelligence.stress_report import compute_field_stress_report
from cultivos.services.intelligence.upcoming_treatments import compute_upcoming_treatments
from cultivos.services.intelligence.carbon import compute_carbon_projection
from cultivos.services.intelligence.field_timeline import compute_field_timeline
from cultivos.services.intelligence.progress_report import compute_progress_report
from cultivos.services.intelligence.regen_trajectory import compute_regen_trajectory
from cultivos.services.intelligence.water_stress import compute_water_stress
from cultivos.services.intelligence.yield_forecast import compute_farm_yield_forecast

router = APIRouter(prefix="/api/farms", tags=["farms"])


# ── Farm CRUD ─────────────────────────────────────────────────────────

@router.post("", response_model=FarmOut, status_code=201)
def create_farm(body: FarmCreate, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))):
    """Create a new farm. Requires admin role."""
    farm = Farm(**body.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("")
def list_farms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List farms with pagination. Farmers only see their own farm; admins see all."""
    query = db.query(Farm)
    if user and hasattr(user, 'role') and user.role == "farmer" and user.farm_id is not None:
        query = query.filter(Farm.id == user.farm_id)
    total = query.count()
    items = query.order_by(Farm.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "data": [FarmOut.model_validate(f) for f in items],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


@router.get("/{farm_id}", response_model=FarmOut)
def get_farm(farm_id: int, db: Session = Depends(get_db)):
    """Retrieve a single farm by ID."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.put("/{farm_id}", response_model=FarmOut)
def update_farm(farm_id: int, body: FarmUpdate, db: Session = Depends(get_db)):
    """Update an existing farm's attributes. Only provided fields are changed."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(farm, key, value)
    db.commit()
    db.refresh(farm)
    return farm


@router.delete("/{farm_id}", status_code=204)
def delete_farm(farm_id: int, db: Session = Depends(get_db)):
    """Permanently delete a farm by ID."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    db.delete(farm)
    db.commit()
    return Response(status_code=204)


# ── Heatmap ──────────────────────────────────────────────────────────

@router.get("/{farm_id}/heatmap", response_model=HeatmapResponse)
def farm_heatmap(farm_id: int, db: Session = Depends(get_db)):
    """Return all fields with centroid + latest health score for map rendering."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    from cultivos.db.models import HealthScore
    from cultivos.utils.geo import calculate_centroid

    fields = db.query(Field).filter(Field.farm_id == farm_id).all()
    points = []
    for field in fields:
        centroid = calculate_centroid(field.boundary_coordinates)
        centroid_lat = centroid[0] if centroid else None
        centroid_lon = centroid[1] if centroid else None

        latest_hs = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == field.id)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )

        points.append(FieldHeatmapPoint(
            field_id=field.id,
            field_name=field.name,
            crop_type=field.crop_type,
            centroid_lat=centroid_lat,
            centroid_lon=centroid_lon,
            health_score=latest_hs.score if latest_hs else None,
            health_trend=latest_hs.trend if latest_hs else None,
        ))

    return HeatmapResponse(farm_id=farm.id, farm_name=farm.name, fields=points)


# ── Field CRUD (nested under farm) ───────────────────────────────────

@router.post("/{farm_id}/fields", response_model=FieldOut, status_code=201)
def create_field(farm_id: int, body: FieldCreate, db: Session = Depends(get_db)):
    """Create a new field under a farm. Automatically computes area from boundary coordinates."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    data = body.model_dump()
    if data.get("boundary_coordinates"):
        from cultivos.utils.geo import calculate_polygon_area_hectares
        data["computed_area_hectares"] = calculate_polygon_area_hectares(data["boundary_coordinates"])
    field = Field(farm_id=farm_id, **data)
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.get("/{farm_id}/fields", response_model=list[FieldOut])
def list_fields(farm_id: int, db: Session = Depends(get_db)):
    """List all fields belonging to a farm, ordered by creation date descending."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return db.query(Field).filter(Field.farm_id == farm_id).order_by(Field.created_at.desc()).all()


@router.get("/{farm_id}/fields/{field_id}", response_model=FieldOut)
def get_field(farm_id: int, field_id: int, db: Session = Depends(get_db)):
    """Retrieve a single field by ID within a given farm."""
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.put("/{farm_id}/fields/{field_id}", response_model=FieldOut)
def update_field(farm_id: int, field_id: int, body: FieldUpdate, db: Session = Depends(get_db)):
    """Update a field's attributes. Recomputes area if boundary coordinates change."""
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    data = body.model_dump(exclude_unset=True)
    if "boundary_coordinates" in data and data["boundary_coordinates"]:
        from cultivos.utils.geo import calculate_polygon_area_hectares
        data["computed_area_hectares"] = calculate_polygon_area_hectares(data["boundary_coordinates"])
    for key, value in data.items():
        setattr(field, key, value)
    db.commit()
    db.refresh(field)
    return field


@router.delete("/{farm_id}/fields/{field_id}", status_code=204)
def delete_field(farm_id: int, field_id: int, db: Session = Depends(get_db)):
    """Permanently delete a field from a farm."""
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    db.delete(field)
    db.commit()
    return Response(status_code=204)


# ── Farm executive summary ────────────────────────────────────────────────

@router.get("/{farm_id}/executive-summary", response_model=FarmExecutiveSummaryOut)
def farm_executive_summary(farm_id: int, db: Session = Depends(get_db)):
    """Per-farm KPI summary: fields, hectares, avg health, treatments, alerts, CO2e, 30-day activity."""
    result = compute_farm_executive_summary(farm_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return result


# ── Seasonal yield forecast ───────────────────────────────────────────────

@router.get("/{farm_id}/yield-forecast", response_model=FarmYieldForecastOut)
def farm_yield_forecast(farm_id: int, db: Session = Depends(get_db)):
    """Per-field seasonal yield forecast based on current health score and PredictionSnapshot."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return compute_farm_yield_forecast(db, farm)


# ── Upcoming treatment schedule ───────────────────────────────────────────

@router.get("/{farm_id}/fields/{field_id}/upcoming-treatments", response_model=list[UpcomingTreatmentOut])
def upcoming_treatments(farm_id: int, field_id: int, db: Session = Depends(get_db)):
    """Suggest up to 3 upcoming treatment windows for a field based on growth stage and treatment history."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")
    return compute_upcoming_treatments(field, db)


# ── Field stress report ───────────────────────────────────────────────────

@router.get("/{farm_id}/fields/{field_id}/stress-report", response_model=FieldStressReportOut)
def field_stress_report(farm_id: int, field_id: int, db: Session = Depends(get_db)):
    """Multi-sensor unified stress index for a field: health + NDVI + thermal + soil."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")
    return compute_field_stress_report(field, db)


# ── Field prioritization ranking ──────────────────────────────────────────

@router.get("/{farm_id}/field-priority", response_model=FieldPriorityOut)
def field_priority(farm_id: int, db: Session = Depends(get_db)):
    """Rank all fields in a farm by urgency — highest stress first.

    Combines multi-sensor stress scores to identify which field needs
    attention most urgently. Farmers with 3+ fields get an AI triage list.
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return compute_field_priority(farm, db)


# ── Disease outbreak risk assessment ─────────────────────────────────────────

@router.get("/{farm_id}/fields/{field_id}/disease-risk-assessment", response_model=DiseaseRiskAssessmentOut)
def disease_risk_assessment(farm_id: int, field_id: int, db: Session = Depends(get_db)):
    """Assess disease outbreak risk combining weather + NDVI + soil + crop type.

    Risk factors: humidity > 70% (+20), NDVI drop > 20% MoM (+25),
    soil pH < 5.5 (+15), temperature > 35°C (+10). Defaults to low risk
    when no weather data is available.
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")
    return compute_disease_risk_assessment(field, db)


# ── Crop growth health report ─────────────────────────────────────────────────

@router.get("/{farm_id}/fields/{field_id}/growth-report", response_model=GrowthReportOut)
def growth_report(farm_id: int, field_id: int, db: Session = Depends(get_db)):
    """Compare crop health against expected phenology stage.

    Uses planting date to determine expected stage and compares latest health
    score against stage baseline. Returns on_track status, health_vs_expected
    ratio, estimated lag_days, and Spanish-language recommendations.
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")
    return compute_growth_report(field, db)


# ── Farmer daily briefing ──────────────────────────────────────────────────────

@router.get("/{farm_id}/daily-briefing", response_model=DailyBriefingOut)
def daily_briefing(farm_id: int, db: Session = Depends(get_db)):
    """Return a concise daily action summary for the farm in Spanish.

    Combines field priority ranking, weather summary, and upcoming treatment
    reminders into a single voice-friendly briefing. overall_farm_status:
    urgent (any field score >= 60), attention (any >= 30), ok otherwise.
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return compute_daily_briefing(farm, db)


# ── Water stress early warning ─────────────────────────────────────────────────

@router.get("/{farm_id}/fields/{field_id}/water-stress", response_model=WaterStressOut)
def water_stress(farm_id: int, field_id: int, db: Session = Depends(get_db)):
    """Assess water stress urgency from soil moisture, thermal stress, and weather.

    Urgency levels: severe (3 factors or soil<20%+temp>35°C), moderate (2 factors
    or soil<20%), low (1 factor), none (0 factors). Graceful degradation when
    soil data is missing.
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")
    return compute_water_stress(field, db)


# ── Predictive risk alert ──────────────────────────────────────────────────────

@router.get("/{farm_id}/fields/{field_id}/forecast-alerts", response_model=ForecastAlertsOut)
def forecast_alerts(farm_id: int, field_id: int, db: Session = Depends(get_db)):
    """Project risk level 3 days ahead using disease risk + health score + weather.

    projected_risk_level: high (disease>=50 or health<40+humidity>70%),
    medium (disease>=25 or health<60 or humidity>60%), low (default).
    No weather data → low risk (safe default).
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")
    return compute_forecast_alerts(field, db)


# ── Regenerative score trajectory ─────────────────────────────────────────────

@router.get("/{farm_id}/regen-trajectory", response_model=RegenTrajectoryOut)
def regen_trajectory(farm_id: int, db: Session = Depends(get_db)):
    """Return monthly regenerative score trajectory for the last 12 months.

    regen_score per month = (organic_treatment_pct * 0.6) + (avg_health_score * 0.4)
    trend: improving | stable | declining (compares last 3 vs first 3 months avg).
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return compute_regen_trajectory(farm, db)


# ── Farm health progress report ───────────────────────────────────────────────

@router.get("/{farm_id}/progress-report", response_model=ProgressReportOut)
def farm_progress_report(
    farm_id: int,
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """Before/after comparison of health score, NDVI, and soil pH across all fields.

    Splits the date range at midpoint and computes deltas (end_avg - start_avg).
    improved=True when health_delta > 0. Useful for longitudinal grant evidence.
    """
    from datetime import date as date_type
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    try:
        start = date_type.fromisoformat(start_date)
        end = date_type.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Dates must be YYYY-MM-DD format")
    return compute_progress_report(farm, start, end, db)


# ── Soil carbon baseline + projection ─────────────────────────────────────────

def _get_field_for_farm(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.post("/{farm_id}/fields/{field_id}/carbon-baseline", response_model=CarbonBaselineOut)
def record_carbon_baseline(
    farm_id: int,
    field_id: int,
    payload: CarbonBaselineIn,
    db: Session = Depends(get_db),
):
    """Record an explicit SOC baseline measurement for carbon finance tracking.

    Stores the measurement date and lab method alongside the SOC percentage.
    Multiple baselines can be recorded; the GET projection always uses the latest.
    """
    from cultivos.db.models import CarbonBaseline
    field = _get_field_for_farm(farm_id, field_id, db)
    baseline = CarbonBaseline(
        field_id=field.id,
        soc_percent=payload.soc_percent,
        measurement_date=payload.measurement_date,
        lab_method=payload.lab_method,
    )
    db.add(baseline)
    db.commit()
    db.refresh(baseline)
    return CarbonBaselineOut(
        id=baseline.id,
        field_id=baseline.field_id,
        soc_percent=baseline.soc_percent,
        measurement_date=baseline.measurement_date,
        lab_method=baseline.lab_method,
    )


@router.get("/{farm_id}/fields/{field_id}/carbon-projection", response_model=CarbonProjectionOut)
def carbon_projection(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Compute 5-year CO2e sequestration projection from the latest SOC baseline.

    Uses 3.67 CO2:C ratio and 0.5 t C/ha/yr regenerative sequestration rate.
    Returns 404 when no baseline has been recorded for this field.
    """
    from cultivos.db.models import CarbonBaseline
    field = _get_field_for_farm(farm_id, field_id, db)
    latest = (
        db.query(CarbonBaseline)
        .filter(CarbonBaseline.field_id == field.id)
        .order_by(CarbonBaseline.measurement_date.desc(), CarbonBaseline.recorded_at.desc())
        .first()
    )
    if latest is None:
        raise HTTPException(status_code=404, detail="No carbon baseline recorded for this field")
    hectares = field.hectares or 0.0
    projection = compute_carbon_projection(
        soc_percent=latest.soc_percent,
        hectares=hectares,
        lab_method=latest.lab_method,
    )
    return CarbonProjectionOut(field_id=field.id, **projection)


# ── Field intervention timeline ───────────────────────────────────────────────

@router.get("/{farm_id}/fields/{field_id}/timeline", response_model=FieldTimelineOut)
def field_timeline(
    farm_id: int,
    field_id: int,
    start_date: Optional[str] = Query(None, description="Filter from YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter to YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """Chronological audit trail of all events for a field.

    Events: health score recordings, NDVI measurements, treatments applied, alerts triggered.
    Sorted by date ASC. Optional start_date/end_date filtering.
    """
    from datetime import date as date_type
    field = _get_field_for_farm(farm_id, field_id, db)
    start = date_type.fromisoformat(start_date) if start_date else None
    end = date_type.fromisoformat(end_date) if end_date else None
    return compute_field_timeline(field, db, start_date=start, end_date=end)
