"""Pydantic schema for field micro-climate summary endpoint."""

from typing import Optional
from pydantic import BaseModel


class FieldMicroclimateOut(BaseModel):
    field_id: int
    period_days: int
    avg_temp_c: Optional[float]
    max_temp_c: Optional[float]
    min_temp_c: Optional[float]
    total_rainfall_mm: float
    avg_humidity_pct: Optional[float]
    avg_wind_speed_kmh: Optional[float]
    frost_risk_days: int
    summary_es: str
