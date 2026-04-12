"""Pydantic models for cooperative monthly progress snapshot."""

from typing import List

from pydantic import BaseModel


class MonthlyProgressEntry(BaseModel):
    month: str  # YYYY-MM
    avg_health: float
    total_treatments: int
    new_observations: int
    regen_score_avg: float
    mom_delta: float  # month-over-month regen_score delta (0.0 for first month)


class CoopMonthlyProgressOut(BaseModel):
    cooperative_id: int
    months_requested: int
    months: List[MonthlyProgressEntry]
    overall_trend: str  # improving | stable | declining
