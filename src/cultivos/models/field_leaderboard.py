from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class FieldLeaderboardEntry(BaseModel):
    rank: int
    farm_name: str
    field_id: int
    crop_type: Optional[str]
    latest_health: Optional[float]
    hectares: float


class FieldLeaderboardOut(BaseModel):
    cooperative_id: int
    total_fields: int
    fields: list[FieldLeaderboardEntry]
