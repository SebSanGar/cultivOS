"""Pydantic schemas for thermal stress analysis endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class ThermalResultCreate(BaseModel):
    thermal_band: list[list[float]] = Field(..., description="2D array of temperature values (Celsius)")
    flight_id: int | None = None


class ThermalResultOut(BaseModel):
    id: int
    field_id: int
    flight_id: int | None
    temp_mean: float
    temp_std: float
    temp_min: float
    temp_max: float
    pixels_total: int
    stress_pct: float
    irrigation_deficit: bool
    analyzed_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
