"""Pydantic schemas for seasonal yield forecast summary."""

from pydantic import BaseModel


class FieldYieldForecast(BaseModel):
    field_id: int
    field_name: str
    crop_type: str | None
    projected_yield_kg: float
    confidence: str  # "high" | "medium" | "low"
    health_score_used: float | None
    has_prediction_snapshot: bool


class FarmYieldForecastOut(BaseModel):
    farm_id: int
    farm_name: str
    fields: list[FieldYieldForecast]
