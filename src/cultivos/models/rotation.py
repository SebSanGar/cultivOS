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
