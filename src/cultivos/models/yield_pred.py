"""Pydantic schemas for yield prediction endpoints."""

from pydantic import BaseModel


class YieldPredictionOut(BaseModel):
    field_id: int
    crop_type: str
    hectares: float
    kg_per_ha: float
    min_kg_per_ha: float
    max_kg_per_ha: float
    total_kg: float
    nota: str
