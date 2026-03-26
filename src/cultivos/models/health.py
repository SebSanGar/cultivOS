"""Pydantic schemas for Health Score endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class HealthScoreOut(BaseModel):
    id: int
    field_id: int
    score: float = Field(..., ge=0, le=100)
    ndvi_mean: float | None
    ndvi_std: float | None
    stress_pct: float | None
    soil_ph: float | None
    soil_organic_matter_pct: float | None
    trend: str
    sources: list[str]
    breakdown: dict[str, float]
    scored_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
