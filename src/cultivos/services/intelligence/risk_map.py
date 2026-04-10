"""Field risk heatmap service — pure computation, no HTTP concerns.

Combines latest health score, weather alerts, disease risk, and thermal stress
into a 0-100 risk score per field. Higher = more risk.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult, ThermalResult, WeatherRecord
from cultivos.models.risk_map import FieldRiskItem
from cultivos.services.crop.disease import assess_disease_weather_risk
from cultivos.services.intelligence.weather_alerts import detect_weather_alerts

# Direct-point contributions (spec: clamp(sum, 0, 100))
# Weather: critica=30pts, moderada=15pts (per alert, capped at 30 total)
_WEATHER_SEVERITY_PTS = {"critica": 30.0, "moderada": 15.0}
_WEATHER_MAX = 30.0

# Disease risk level → direct points
_DISEASE_SCORE = {
    "sin_riesgo": 0.0,
    "bajo": 5.0,
    "moderado": 15.0,
    "medio": 15.0,
    "alto": 25.0,
    "critico": 25.0,
}

# Thermal: scale stress_pct (0-100) to max 20 pts
_THERMAL_MAX = 20.0


def _centroid(boundary_coordinates: list) -> tuple[float, float] | tuple[None, None]:
    """Return (lat, lon) centroid of a [[lon, lat], ...] polygon, or (None, None)."""
    if not boundary_coordinates or len(boundary_coordinates) < 1:
        return None, None
    lons = [c[0] for c in boundary_coordinates]
    lats = [c[1] for c in boundary_coordinates]
    return sum(lats) / len(lats), sum(lons) / len(lons)


def _compute_weather_component(farm_id: int, db: Session) -> float | None:
    """Return weather risk score (0-100) from latest weather record, or None."""
    record = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )
    if not record:
        return None
    alerts = detect_weather_alerts(
        temp_c=record.temp_c,
        humidity_pct=record.humidity_pct,
        wind_kmh=record.wind_kmh,
        rainfall_mm=record.rainfall_mm,
        description=record.description or "",
        forecast_3day=record.forecast_3day or [],
    )
    if not alerts:
        return 0.0
    total = sum(_WEATHER_SEVERITY_PTS.get(a.get("severity", ""), 0.0) for a in alerts)
    return min(total, _WEATHER_MAX)


def _compute_disease_component(field: Field, farm_id: int, db: Session) -> float | None:
    """Return disease risk score (0-100), or None if no NDVI data."""
    ndvi = (
        db.query(NDVIResult)
        .filter(NDVIResult.field_id == field.id)
        .order_by(NDVIResult.id.desc())
        .first()
    )
    if not ndvi:
        return None

    thermal = (
        db.query(ThermalResult)
        .filter(ThermalResult.field_id == field.id)
        .order_by(ThermalResult.id.desc())
        .first()
    )
    weather = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )

    result = assess_disease_weather_risk(
        ndvi_mean=ndvi.ndvi_mean,
        stress_pct=ndvi.stress_pct,
        thermal_stress_pct=thermal.stress_pct if thermal else 0.0,
        thermal_temp_mean=thermal.temp_mean if thermal else 25.0,
        ndvi_std=ndvi.ndvi_std,
        humidity_pct=weather.humidity_pct if weather else 50.0,
        rainfall_mm=weather.rainfall_mm if weather else 0.0,
        temp_c=weather.temp_c if weather else 25.0,
    )
    risk_level = result.get("risk_level", "sin_riesgo")
    return _DISEASE_SCORE.get(risk_level, 0.0)


def _compute_thermal_component(field: Field, db: Session) -> float | None:
    """Return thermal risk score (0-100), or None if no thermal data."""
    thermal = (
        db.query(ThermalResult)
        .filter(ThermalResult.field_id == field.id)
        .order_by(ThermalResult.id.desc())
        .first()
    )
    if not thermal:
        return None
    return round(thermal.stress_pct * _THERMAL_MAX / 100.0, 1)


def compute_farm_risk_map(farm_id: int, db: Session) -> list[FieldRiskItem]:
    """Compute risk assessment for every field in a farm.

    Returns one FieldRiskItem per field.  Fields with no data at all
    (no HealthScore, no NDVI, no ThermalResult) receive null risk_score
    and null dominant_factor.
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        raise ValueError(f"Farm {farm_id} not found")

    fields = db.query(Field).filter(Field.farm_id == farm_id).all()
    weather_component = _compute_weather_component(farm_id, db)

    items: list[FieldRiskItem] = []

    for field in fields:
        # --- coordinates ---
        if field.boundary_coordinates:
            lat, lon = _centroid(field.boundary_coordinates)
        else:
            lat = farm.location_lat
            lon = farm.location_lon

        # --- health component (inverted: low health = high risk) ---
        latest_health = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == field.id)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )
        health_component: float | None = (100.0 - latest_health.score) if latest_health else None

        # --- disease and thermal ---
        disease_component = _compute_disease_component(field, farm_id, db)
        thermal_component = _compute_thermal_component(field, db)

        # --- check if there's any data at all ---
        has_data = any(c is not None for c in [health_component, disease_component, thermal_component])
        if not has_data and weather_component is None:
            items.append(FieldRiskItem(
                field_id=field.id,
                name=field.name,
                lat=lat,
                lon=lon,
                risk_score=None,
                dominant_factor=None,
            ))
            continue

        # --- use 0 for missing components when computing score ---
        h = health_component if health_component is not None else 0.0
        w = weather_component if weather_component is not None else 0.0
        d = disease_component if disease_component is not None else 0.0
        t = thermal_component if thermal_component is not None else 0.0

        # Direct-point addition per spec
        risk_score = round(max(0.0, min(100.0, h + w + d + t)), 1)

        # --- dominant factor: whichever component contributed most points ---
        contributions = {
            "health": h,
            "weather": w,
            "disease": d,
            "thermal": t,
        }
        dominant_factor = max(contributions, key=lambda k: contributions[k])

        items.append(FieldRiskItem(
            field_id=field.id,
            name=field.name,
            lat=lat,
            lon=lon,
            risk_score=risk_score,
            dominant_factor=dominant_factor,
        ))

    return items
