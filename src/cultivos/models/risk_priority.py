"""Pydantic models for risk-weighted field priority list endpoint."""

from pydantic import BaseModel


class RiskPriorityItem(BaseModel):
    field_id: int
    crop_type: str
    stress_score: float        # composite stress index 0-100
    days_since_treatment: int  # capped at 90; 90 when no treatment history
    priority_score: float      # stress_score * min(days, 90) / 90; 0-100
    recommendation_es: str
