"""Pydantic schemas for Rotation endpoints."""

from pydantic import BaseModel


class RotationSeasonOut(BaseModel):
    season: str
    crop: str
    reason: str
    purpose: str
    months: str


class RotationPlanOut(BaseModel):
    field_id: int
    last_crop: str
    region: str
    plan: list[RotationSeasonOut]


class MultiYearSeasonOut(BaseModel):
    year: int
    season: str
    crop: str
    reason: str
    purpose: str
    months: str
    organic_matter_pct: float


class MultiYearPlanOut(BaseModel):
    field_id: int
    last_crop: str
    region: str
    plan: list[MultiYearSeasonOut]
    total_years: int
    milpa_recommended: bool
    milpa_description: str
    om_start: float
    om_end: float
