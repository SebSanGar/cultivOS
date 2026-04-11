"""Pydantic response model for GET /api/farms/{farm_id}/progress-report."""

from typing import Optional
from pydantic import BaseModel


class FieldProgressItem(BaseModel):
    field_id: int
    field_name: str
    health_delta: Optional[float]   # None if data missing in one half
    ndvi_delta: Optional[float]
    soil_ph_delta: Optional[float]
    improved: Optional[bool]        # None if health_delta is None


class ProgressReportOut(BaseModel):
    period_start: str               # "YYYY-MM-DD"
    period_end: str
    fields: list[FieldProgressItem]
    farms_improved_pct: float       # 0-100
