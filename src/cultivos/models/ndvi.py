"""Pydantic schemas for NDVI analysis endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class NDVIZoneOut(BaseModel):
    classification: str
    min_ndvi: float
    max_ndvi: float
    pixel_count: int
    percentage: float


class NDVIResultCreate(BaseModel):
    nir_band: list[list[float]] = Field(..., description="2D array of NIR reflectance values")
    red_band: list[list[float]] = Field(..., description="2D array of Red reflectance values")
    flight_id: int | None = None


class NDVIResultOut(BaseModel):
    id: int
    field_id: int
    flight_id: int | None
    ndvi_mean: float
    ndvi_std: float
    ndvi_min: float
    ndvi_max: float
    pixels_total: int
    stress_pct: float
    zones: list[NDVIZoneOut]
    analyzed_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
