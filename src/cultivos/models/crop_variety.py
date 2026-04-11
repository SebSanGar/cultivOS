"""Pydantic schemas for Jalisco/LATAM crop variety knowledge base."""

from pydantic import BaseModel


class CropVarietyOut(BaseModel):
    id: int
    crop_name: str
    name: str
    region: str
    altitude_m: int | None = None
    water_mm: int | None = None
    diseases: list[str] = []
    adaptation_notes: str | None = None

    model_config = {"from_attributes": True}
