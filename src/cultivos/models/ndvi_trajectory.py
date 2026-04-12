"""Pydantic response model for field NDVI 90-day trajectory endpoint."""

from typing import List, Optional
from pydantic import BaseModel


class NDVIMonthOut(BaseModel):
    month_label: str               # "YYYY-MM"
    avg_ndvi: Optional[float]
    avg_stress_pct: Optional[float]


class NDVITrajectoryOut(BaseModel):
    field_id: int
    months: List[NDVIMonthOut]
    ndvi_trend: str                # improving | stable | declining
    stress_trend: str              # improving (stress decreasing) | stable | declining
