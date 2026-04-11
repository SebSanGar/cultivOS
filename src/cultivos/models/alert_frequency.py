"""Pydantic response models for alert frequency analysis."""

from pydantic import BaseModel


class AlertFrequencyFieldItem(BaseModel):
    field_id: int
    field_name: str
    monthly_avg: float
    dominant_type: str | None
    trend: str  # increasing | stable | decreasing


class AlertFrequencyOut(BaseModel):
    farm_id: int
    fields: list[AlertFrequencyFieldItem]
    overall_alert_load: float
