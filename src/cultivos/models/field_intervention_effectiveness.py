"""Pydantic response models for field intervention effectiveness endpoint (#206)."""

from typing import Optional

from pydantic import BaseModel


class TreatmentEffectivenessRanked(BaseModel):
    name: str
    avg_delta: float


class FieldInterventionEffectivenessOut(BaseModel):
    field_id: int
    period_days: int
    treatments_evaluated: int
    effective_count: int
    neutral_count: int
    counterproductive_count: int
    effectiveness_rate_pct: float
    best_treatment: Optional[TreatmentEffectivenessRanked]
    worst_treatment: Optional[TreatmentEffectivenessRanked]
    recommendation_es: str
