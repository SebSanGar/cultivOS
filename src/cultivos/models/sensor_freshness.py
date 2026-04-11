"""Pydantic models for sensor data freshness response."""

from __future__ import annotations

from pydantic import BaseModel


class FieldFreshnessItem(BaseModel):
    field_id: int
    crop_type: str
    ndvi_days_ago: int | None
    soil_days_ago: int | None
    health_days_ago: int | None
    weather_days_ago: int | None
    stale_sensors: list[str]


class SensorFreshnessOut(BaseModel):
    farm_id: int
    checked_at: str  # ISO 8601
    fields: list[FieldFreshnessItem]
