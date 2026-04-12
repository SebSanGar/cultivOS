"""Pydantic models for cooperative data completeness aggregate."""

from typing import Optional

from pydantic import BaseModel


class WorstFarmEntry(BaseModel):
    farm_id: int
    farm_name: str
    farm_score: float


class GradeCounts(BaseModel):
    A: int
    B: int
    C: int
    D: int


class CoopDataCompletenessOut(BaseModel):
    cooperative_id: int
    total_farms: int
    overall_completeness_pct: float
    worst_farm: Optional[WorstFarmEntry]
    farms_by_grade: GradeCounts
