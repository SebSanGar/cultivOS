"""Pydantic response model for field soil health trajectory endpoint."""

from typing import List, Optional
from pydantic import BaseModel


class SoilMonthOut(BaseModel):
    month_label: str            # "YYYY-MM"
    avg_ph: Optional[float]
    avg_organic_matter_pct: Optional[float]


class SoilTrajectoryOut(BaseModel):
    field_id: int
    months: List[SoilMonthOut]
    ph_trend: str               # improving | stable | declining
    organic_matter_trend: str   # improving | stable | declining
