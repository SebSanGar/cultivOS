"""Pydantic models for cooperative regen practice adoption rate endpoint."""

from pydantic import BaseModel


class RegenAdoptionFarm(BaseModel):
    farm_id: int
    farm_name: str
    regen_score: float  # most recent month regen_score from trajectory (0-100)
    treatment_count: int  # total TreatmentRecords within the period


class RegenAdoptionOut(BaseModel):
    cooperative_id: int
    period_days: int
    overall_regen_score_avg: float
    farms: list[RegenAdoptionFarm]
