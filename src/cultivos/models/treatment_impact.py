"""Pydantic response models for farm treatment impact summary endpoint."""

from pydantic import BaseModel


class TreatmentImpactItem(BaseModel):
    crop_type: str
    problema: str
    count: int
    avg_health_delta: float
    interpretation_es: str


class TreatmentImpactOut(BaseModel):
    farm_id: int
    period_days: int
    treatments: list[TreatmentImpactItem]
