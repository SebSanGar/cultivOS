"""Pydantic response model for GET /api/farms/{farm_id}/fields/{field_id}/growth-report."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class GrowthReportOut(BaseModel):
    field_id: int
    crop_type: Optional[str]
    current_stage: Optional[str]       # e.g. "floracion" — None if no planting date
    expected_stage: Optional[str]      # same as current_stage (time-based phenology)
    on_track: Optional[bool]           # None when no health data or no planting date
    health_vs_expected: Optional[float]  # ratio actual/expected health; None if no data
    lag_days: int                      # estimated days behind schedule (0 = on track)
    recommendations: list[str]         # Spanish-language action items
