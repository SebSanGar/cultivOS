"""Pydantic schemas for seasonal TEK calendar alerts."""

from typing import Optional

from pydantic import BaseModel


class SeasonalAlertOut(BaseModel):
    crop: str
    alert_type: str  # preparacion, siembra, cosecha, mantenimiento
    message: str
    season: str  # temporal, secas
    month_range: str  # e.g. "Mar-Abr"


class FieldHealthSummary(BaseModel):
    field_id: int
    field_name: str
    crop_type: Optional[str] = None
    score: float
    trend: Optional[str] = None


class SeasonalAlertsResponse(BaseModel):
    farm_id: int
    season: str
    reference_date: str
    alerts: list[SeasonalAlertOut]
    field_health: list[FieldHealthSummary] = []
    avg_health: Optional[float] = None
