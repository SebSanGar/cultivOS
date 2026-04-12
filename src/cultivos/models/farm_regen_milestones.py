"""Pydantic models for farm regenerative milestone tracker."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MilestoneOut(BaseModel):
    name: str
    achieved: bool
    achieved_at: Optional[datetime]
    description_es: str


class FarmRegenMilestonesOut(BaseModel):
    farm_id: int
    milestones: list[MilestoneOut]
    milestones_achieved_count: int
    next_milestone_es: str
    progress_to_next_pct: float
