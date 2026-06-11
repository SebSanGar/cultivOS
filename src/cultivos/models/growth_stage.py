"""Pydantic schemas for crop growth stage endpoint."""

from pydantic import BaseModel


class StageInfoOut(BaseModel):
    name: str
    name_es: str
    name_en: str
    start_day: int
    end_day: int
    water_multiplier: float
    nutrient_focus: str
    nutrient_focus_en: str
    is_current: bool


class GrowthStageOut(BaseModel):
    crop_type: str
    stage: str
    stage_es: str
    stage_en: str
    days_since_planting: int
    days_in_stage: int
    days_until_next_stage: int | None
    water_multiplier: float
    nutrient_focus: str
    nutrient_focus_en: str
    all_stages: list[StageInfoOut] = []
