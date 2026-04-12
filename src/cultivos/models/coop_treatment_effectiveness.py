"""Pydantic models for cooperative treatment effectiveness aggregate."""

from pydantic import BaseModel


class CoopTreatmentGroup(BaseModel):
    crop_type: str
    treatment_summary: str
    avg_health_delta: float
    usage_count: int
    participating_farms_count: int


class CoopTreatmentEffectivenessOut(BaseModel):
    cooperative_id: int
    groups: list[CoopTreatmentGroup]
