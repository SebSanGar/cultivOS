"""Pydantic schemas for crop types."""

from pydantic import BaseModel


class CropTypeOut(BaseModel):
    id: int
    name: str
    family: str
    growing_season: str
    water_needs: str
    regions: list[str]
    companions: list[str]
    days_to_harvest: int | None = None
    optimal_temp_min: float | None = None
    optimal_temp_max: float | None = None
    description_es: str

    model_config = {"from_attributes": True}
