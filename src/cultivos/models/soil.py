"""Pydantic schemas for Soil Analysis endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class SoilAnalysisCreate(BaseModel):
    ph: float | None = Field(None, ge=0, le=14)
    organic_matter_pct: float | None = Field(None, ge=0, le=100)
    nitrogen_ppm: float | None = Field(None, ge=0)
    phosphorus_ppm: float | None = Field(None, ge=0)
    potassium_ppm: float | None = Field(None, ge=0)
    texture: str | None = None
    moisture_pct: float | None = Field(None, ge=0, le=100)
    electrical_conductivity: float | None = Field(None, ge=0)
    depth_cm: float | None = Field(None, ge=0)
    notes: str | None = None
    recommendations: str | None = None
    sampled_at: datetime


class SoilAnalysisUpdate(BaseModel):
    ph: float | None = Field(None, ge=0, le=14)
    organic_matter_pct: float | None = Field(None, ge=0, le=100)
    nitrogen_ppm: float | None = Field(None, ge=0)
    phosphorus_ppm: float | None = Field(None, ge=0)
    potassium_ppm: float | None = Field(None, ge=0)
    texture: str | None = None
    moisture_pct: float | None = Field(None, ge=0, le=100)
    electrical_conductivity: float | None = Field(None, ge=0)
    depth_cm: float | None = Field(None, ge=0)
    notes: str | None = None
    recommendations: str | None = None
    sampled_at: datetime | None = None


class SoilAnalysisOut(BaseModel):
    id: int
    field_id: int
    ph: float | None
    organic_matter_pct: float | None
    nitrogen_ppm: float | None
    phosphorus_ppm: float | None
    potassium_ppm: float | None
    texture: str | None
    moisture_pct: float | None
    electrical_conductivity: float | None
    depth_cm: float | None
    notes: str | None
    recommendations: str | None
    sampled_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
