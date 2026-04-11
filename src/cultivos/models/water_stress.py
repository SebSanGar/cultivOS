"""Pydantic response model for GET /api/farms/{farm_id}/fields/{field_id}/water-stress."""

from __future__ import annotations
from pydantic import BaseModel


class WaterStressOut(BaseModel):
    urgency_level: str  # none | low | moderate | severe
    contributing_factors: list[str]
    recommended_action_es: str
    next_check_hours: int
