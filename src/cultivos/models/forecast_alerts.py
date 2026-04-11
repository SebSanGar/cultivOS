"""Pydantic response model for GET /api/farms/{farm_id}/fields/{field_id}/forecast-alerts."""

from __future__ import annotations
from pydantic import BaseModel


class ForecastAlertsOut(BaseModel):
    field_id: int
    forecast_date: str  # ISO date string (today + 3 days)
    projected_risk_level: str  # low | medium | high
    risk_drivers: list[str]
    preventive_actions_es: list[str]
