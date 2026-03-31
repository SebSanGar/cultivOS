"""Pydantic schemas for intervention scoring endpoints."""

from typing import Optional

from pydantic import BaseModel


class InterventionScoreOut(BaseModel):
    problema: str
    tratamiento: str
    costo_estimado_mxn: int
    urgencia: str
    health_score_used: float
    expected_health_delta: float
    success_probability: float
    cost_per_hectare: float
    intervention_score: float
    metodo_ancestral: Optional[str] = None
    scientific_basis: Optional[str] = None
