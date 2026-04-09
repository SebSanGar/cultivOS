"""Pydantic schemas for Weather endpoints."""

from datetime import datetime

from pydantic import BaseModel


class ForecastDay(BaseModel):
    temp_c: float
    humidity_pct: float
    wind_kmh: float
    description: str
    rainfall_mm: float = 0.0


class WeatherRecordCreate(BaseModel):
    temp_c: float
    humidity_pct: float
    wind_kmh: float
    description: str
    rainfall_mm: float = 0.0
    forecast_3day: list[ForecastDay] = []


class WeatherRecordOut(BaseModel):
    id: int
    farm_id: int
    temp_c: float
    humidity_pct: float
    wind_kmh: float
    rainfall_mm: float
    description: str
    forecast_3day: list[ForecastDay]
    recorded_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class WeatherAlertOut(BaseModel):
    alert_type: str
    severity: str
    title: str
    message: str
    actions: list[str]
    source: str


class WeatherAlertsResponse(BaseModel):
    farm_id: int
    alerts: list[WeatherAlertOut]
    weather_record_id: int | None = None
