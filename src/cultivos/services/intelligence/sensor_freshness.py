"""Sensor data freshness service.

For each field in a farm, reports how many days have passed since the most
recent record from each of four data sources:
  - NDVIResult  (field-level,  analyzed_at)
  - SoilAnalysis (field-level, sampled_at)
  - HealthScore  (field-level, scored_at)
  - WeatherRecord (farm-level, recorded_at)

Stale threshold: >14 days (or no data at all).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult, SoilAnalysis, WeatherRecord

_STALE_DAYS = 14


def _days_ago(dt: datetime | None, now: datetime) -> int | None:
    if dt is None:
        return None
    delta = now - dt.replace(tzinfo=None) if dt.tzinfo else now - dt
    return max(0, delta.days)


def compute_sensor_freshness(farm: Farm, db: Session) -> dict:
    """Compute sensor data freshness for all fields on a farm."""
    now = datetime.utcnow()

    # Farm-level weather — one query, used for all fields
    weather_row = (
        db.query(func.max(WeatherRecord.recorded_at))
        .filter(WeatherRecord.farm_id == farm.id)
        .scalar()
    )
    weather_days = _days_ago(weather_row, now)

    # All fields for this farm
    fields = db.query(Field).filter(Field.farm_id == farm.id).all()

    field_items: list[dict] = []
    for field in fields:
        # Latest NDVI
        ndvi_dt = (
            db.query(func.max(NDVIResult.analyzed_at))
            .filter(NDVIResult.field_id == field.id)
            .scalar()
        )
        ndvi_days = _days_ago(ndvi_dt, now)

        # Latest soil
        soil_dt = (
            db.query(func.max(SoilAnalysis.sampled_at))
            .filter(SoilAnalysis.field_id == field.id)
            .scalar()
        )
        soil_days = _days_ago(soil_dt, now)

        # Latest health score
        health_dt = (
            db.query(func.max(HealthScore.scored_at))
            .filter(HealthScore.field_id == field.id)
            .scalar()
        )
        health_days = _days_ago(health_dt, now)

        # Build stale list
        stale: list[str] = []
        if ndvi_days is None or ndvi_days > _STALE_DAYS:
            stale.append("ndvi")
        if soil_days is None or soil_days > _STALE_DAYS:
            stale.append("soil")
        if health_days is None or health_days > _STALE_DAYS:
            stale.append("health")
        if weather_days is None or weather_days > _STALE_DAYS:
            stale.append("weather")

        field_items.append({
            "field_id": field.id,
            "crop_type": field.crop_type or "",
            "ndvi_days_ago": ndvi_days,
            "soil_days_ago": soil_days,
            "health_days_ago": health_days,
            "weather_days_ago": weather_days,
            "stale_sensors": stale,
        })

    return {
        "farm_id": farm.id,
        "checked_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fields": field_items,
    }
