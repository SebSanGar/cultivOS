"""Pydantic response model for treatment outcomes endpoint."""

from pydantic import BaseModel


class TreatmentOutcomeItem(BaseModel):
    crop_type: str
    treatment_summary: str
    avg_health_delta: float
    usage_count: int
