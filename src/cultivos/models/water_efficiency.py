"""Pydantic models for water use efficiency report."""

from pydantic import BaseModel


class WaterEfficiencyOut(BaseModel):
    field_id: int
    field_hectares: float
    crop_type: str
    water_stress_index: float
    optimal_irrigation_mm: float
    liters_wasted: float
    recomendacion: str
