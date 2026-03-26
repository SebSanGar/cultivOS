"""Pydantic schemas for Weather endpoints."""

from datetime import datetime

from pydantic import BaseModel


class ForecastDay(BaseModel):
    temp_c: float
    humidity_pct: float
    wind_kmh: float
    description: str


class WeatherRecordCreate(BaseModel):
    temp_c: float
    humidity_pct: float
    wind_kmh: float
    description: str
    forecast_3day: list[ForecastDay] = []


class WeatherRecordOut(BaseModel):
    id: int
    farm_id: int
    temp_c: float
    humidity_pct: float
    wind_kmh: float
    description: str
    forecast_3day: list[ForecastDay]
    recorded_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
