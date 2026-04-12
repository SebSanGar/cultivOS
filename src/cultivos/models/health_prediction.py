"""Pydantic models for #187 — Field 30-day health prediction."""

from pydantic import BaseModel


class HealthPredictionOut(BaseModel):
    field_id: int
    current_avg_health: float
    predicted_health_30d: float
    trend_direction: str  # improving, stable, declining
    confidence: str  # high, medium, low
    risk_flag: bool
    data_points: int
