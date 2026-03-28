"""Pydantic schemas for the action timeline endpoint."""

from typing import Any, Optional

from pydantic import BaseModel


class WeatherSummary(BaseModel):
    total_rainfall_mm: float
    max_temp_c: float
    min_temp_c: float
    rainy_days: int
    forecast_days: int


class TimelineAction(BaseModel):
    source: str  # seasonal_calendar, growth_stage, treatment
    priority: int
    action_type: str  # preparacion, siembra, cosecha, mantenimiento, cuidado, tratamiento
    description: str
    weather_note: Optional[str] = None

    # Optional fields depending on source
    crop: Optional[str] = None
    season: Optional[str] = None
    month_range: Optional[str] = None
    stage: Optional[str] = None
    stage_es: Optional[str] = None
    days_in_stage: Optional[int] = None
    days_until_next_stage: Optional[int] = None
    water_multiplier: Optional[float] = None
    treatment_id: Optional[int] = None
    problema: Optional[str] = None
    urgencia: Optional[str] = None
    costo_estimado_mxn: Optional[int] = None


class ActionTimelineOut(BaseModel):
    reference_date: str
    crop_type: Optional[str] = None
    action_count: int
    weather_summary: Optional[WeatherSummary] = None
    actions: list[TimelineAction]
