"""Pydantic response model for GET /api/farms/{farm_id}/regen-trajectory."""

from pydantic import BaseModel


class RegenMonthEntry(BaseModel):
    month: str                   # "YYYY-MM"
    organic_treatment_pct: float  # 0-100
    avg_health_score: float       # 0-100 (0 if no health data)
    treatment_count: int
    regen_score: float            # organic_pct * 0.6 + avg_health_score * 0.4


class RegenTrajectoryOut(BaseModel):
    farm_id: int
    months: list[RegenMonthEntry]
    trend: str                   # "improving" | "stable" | "declining"
