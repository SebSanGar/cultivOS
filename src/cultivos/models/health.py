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
    trend: str | None = None
    sources: list[str]
    breakdown: dict[str, float]
    scored_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthHistoryOut(BaseModel):
    """Health score history with computed overall trend."""
    scores: list[HealthScoreOut]
    trend: str  # improving, stable, declining, insufficient_data
    count: int


class HealthTrendOut(BaseModel):
    """Health trend analysis with rate of change and projection."""
    trend: str  # improving, stable, declining, insufficient_data
    rate_of_change: float  # slope per observation interval
    projection: float | None  # projected next score (0-100), None if insufficient data
    data_points: int


class TreatmentLink(BaseModel):
    """A treatment that correlates with a health score change."""
    treatment_id: int
    tratamiento: str
    problema: str
    applied_at: datetime | None
    health_before: float
    health_after: float
    delta: float  # positive = improvement


class HealthTrajectoryOut(BaseModel):
    """Health trajectory analysis with trend, rate, projection, and treatment correlations."""
    field_id: int
    trend: str  # improving, stable, declining, insufficient_data
    rate_of_change: float
    projection: float | None
    data_points: int
    current_score: float | None
    score_range: dict  # {"min": float, "max": float}
    treatment_links: list[TreatmentLink]
    scores: list[HealthScoreOut]
