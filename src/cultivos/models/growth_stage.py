"""Pydantic schemas for crop growth stage endpoint."""

from pydantic import BaseModel


class GrowthStageOut(BaseModel):
    crop_type: str
    stage: str
    stage_es: str
    days_since_planting: int
    days_in_stage: int
    days_until_next_stage: int | None
    water_multiplier: float
    nutrient_focus: str
