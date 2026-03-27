"""Pydantic schemas for Farm and Field endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ── Farm ──────────────────────────────────────────────────────────────

class FarmCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    owner_name: str | None = None
    location_lat: float | None = None
    location_lon: float | None = None
    total_hectares: float = 0
    municipality: str | None = None
    state: str = "Jalisco"
    country: str = "MX"


class FarmUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    owner_name: str | None = None
    location_lat: float | None = None
    location_lon: float | None = None
    total_hectares: float | None = None
    municipality: str | None = None
    state: str | None = None
    country: str | None = None


class FarmOut(BaseModel):
    id: int
    name: str
    owner_name: str | None
    location_lat: float | None
    location_lon: float | None
    total_hectares: float
    municipality: str | None
    state: str
    country: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Field ─────────────────────────────────────────────────────────────

class FieldCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    crop_type: str | None = None
    hectares: float = 0
    boundary_coordinates: list[list[float]] | None = None

    @field_validator("boundary_coordinates")
    @classmethod
    def validate_boundary(cls, v: list[list[float]] | None) -> list[list[float]] | None:
        if v is None:
            return v
        if len(v) < 3:
            raise ValueError("Boundary must have at least 3 coordinate pairs")
        for point in v:
            if len(point) != 2:
                raise ValueError("Each coordinate must be [longitude, latitude]")
        return v


class FieldUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    crop_type: str | None = None
    hectares: float | None = None
    boundary_coordinates: list[list[float]] | None = None

    @field_validator("boundary_coordinates")
    @classmethod
    def validate_boundary(cls, v: list[list[float]] | None) -> list[list[float]] | None:
        if v is None:
            return v
        if len(v) < 3:
            raise ValueError("Boundary must have at least 3 coordinate pairs")
        for point in v:
            if len(point) != 2:
                raise ValueError("Each coordinate must be [longitude, latitude]")
        return v


class FieldOut(BaseModel):
    id: int
    farm_id: int
    name: str
    crop_type: str | None
    hectares: float
    boundary_coordinates: list[list[float]] | None
    computed_area_hectares: float | None
    created_at: datetime

    model_config = {"from_attributes": True}
