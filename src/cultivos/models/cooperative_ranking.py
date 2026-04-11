"""Pydantic schema for cooperative member farm ranking endpoint."""

from typing import List
from pydantic import BaseModel


class CooperativeMemberOut(BaseModel):
    farm_id: int
    farm_name: str
    composite_score: float
    rank: int
    health_avg: float
    regen_score: float
    alert_response_rate: float


class CooperativeRankingOut(BaseModel):
    cooperative_id: int
    members: List[CooperativeMemberOut]
