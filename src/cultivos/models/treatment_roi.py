"""Pydantic response models for farm treatment ROI analysis endpoint (#203)."""

from typing import Optional

from pydantic import BaseModel


class TreatmentROIItem(BaseModel):
    treatment_type: str
    count: int
    total_cost_mxn: int
    avg_health_delta: float
    cost_per_health_point: Optional[float]
    recommendation_es: str


class TreatmentROIOut(BaseModel):
    farm_id: int
    period_days: int
    treatments: list[TreatmentROIItem]
    best_roi_treatment: Optional[str]
    worst_roi_treatment: Optional[str]
