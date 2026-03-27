"""Pydantic schemas for seasonal TEK calendar alerts."""

from pydantic import BaseModel


class SeasonalAlertOut(BaseModel):
    crop: str
    alert_type: str  # preparacion, siembra, cosecha, mantenimiento
    message: str
    season: str  # temporal, secas
    month_range: str  # e.g. "Mar-Abr"


class SeasonalAlertsResponse(BaseModel):
    farm_id: int
    season: str
    reference_date: str
    alerts: list[SeasonalAlertOut]
