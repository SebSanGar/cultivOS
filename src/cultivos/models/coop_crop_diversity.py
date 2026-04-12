"""Pydantic models for cooperative crop diversity score."""

from pydantic import BaseModel


class TopCropEntry(BaseModel):
    crop_type: str
    hectares: float
    pct: float


class CoopFarmDiversityEntry(BaseModel):
    farm_id: int
    farm_name: str
    distinct_crops: int
    crop_types: list[str]


class CoopCropDiversityOut(BaseModel):
    cooperative_id: int
    total_farms: int
    total_fields: int
    distinct_crops_coop: int
    shannon_index: float
    top_crops: list[TopCropEntry]
    farms: list[CoopFarmDiversityEntry]
