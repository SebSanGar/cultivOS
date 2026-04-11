"""Pydantic response model for alert response effectiveness."""

from pydantic import BaseModel


class AlertEffectivenessOut(BaseModel):
    farm_id: int
    alerts_analyzed: int
    alerts_with_followup: int
    improvement_rate_pct: float
    avg_improvement_pts: float
