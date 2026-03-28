"""Pydantic models for regenerative practice verification."""

from pydantic import BaseModel


class RegenerativeBreakdown(BaseModel):
    organic_treatments: float
    ancestral_methods: float
    soil_organic_trend: float
    microbiome_health: float
    treatment_diversity: float


class RegenerativeScoreOut(BaseModel):
    score: float
    breakdown: RegenerativeBreakdown
    recommendations: list[str]
