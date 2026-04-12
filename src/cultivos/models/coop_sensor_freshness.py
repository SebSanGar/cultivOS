"""Pydantic models for cooperative sensor freshness rollup."""

from __future__ import annotations

from pydantic import BaseModel


class AvgDaysBySensor(BaseModel):
    ndvi: float | None
    soil: float | None
    health: float | None
    weather: float | None


class CoopFarmFreshnessItem(BaseModel):
    farm_id: int
    farm_name: str
    total_fields: int
    stale_fields: int
    stale_fields_pct: float


class CoopWorstFarm(BaseModel):
    farm_id: int
    farm_name: str
    total_fields: int
    stale_fields: int
    stale_fields_pct: float


class CoopSensorFreshnessOut(BaseModel):
    cooperative_id: int
    farms_count: int
    total_fields: int
    fields_with_stale_sensors: int
    avg_days_since_last_signal: AvgDaysBySensor
    worst_farm: CoopWorstFarm | None
    farms: list[CoopFarmFreshnessItem]
