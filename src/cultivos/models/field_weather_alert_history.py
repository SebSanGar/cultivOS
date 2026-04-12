"""Pydantic schemas for the field weather-alert history endpoint (#209)."""

from __future__ import annotations

from pydantic import BaseModel


class WeatherAlertTypeSummary(BaseModel):
    alert_type: str
    count: int
    last_alert_at: str | None
    dominant_severity: str


class FieldWeatherAlertHistoryOut(BaseModel):
    field_id: int
    period_days: int
    total_alerts: int
    by_type: list[WeatherAlertTypeSummary]
    most_frequent_type: str | None
    alerts_per_month_avg: float
    trend: str  # rising | falling | stable
