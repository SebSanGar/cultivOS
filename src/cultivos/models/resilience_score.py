"""Pydantic models for crop resilience score endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class ResilienceComponents(BaseModel):
    health: float | None
    soil_ph: float | None
    water_stress: float | None
    disease_risk: float | None


class ResilienceScoreOut(BaseModel):
    field_id: int
    resilience_score: float
    components: ResilienceComponents
    interpretation_es: str
