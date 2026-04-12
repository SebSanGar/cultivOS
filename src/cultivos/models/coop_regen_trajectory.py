"""Pydantic schemas for cooperative regen trajectory aggregate endpoint."""

from pydantic import BaseModel


class CoopRegenMonthEntry(BaseModel):
    month: str
    avg_regen_score: float
    farms_contributing: int


class CoopRegenFarmEntry(BaseModel):
    farm_id: int
    farm_name: str
    months_count: int
    latest_regen_score: float
    trend: str


class CoopRegenTrajectoryOut(BaseModel):
    cooperative_id: int
    overall_months: list[CoopRegenMonthEntry]
    overall_trend: str
    farms_count: int
    farms: list[CoopRegenFarmEntry]
