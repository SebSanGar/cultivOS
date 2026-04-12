"""Pydantic response model for field soil nutrient trajectory endpoint (#220)."""

from typing import List, Optional
from pydantic import BaseModel


class SoilNutrientMonthOut(BaseModel):
    month_label: str                        # "YYYY-MM"
    avg_nitrogen_ppm: Optional[float]
    avg_phosphorus_ppm: Optional[float]
    avg_potassium_ppm: Optional[float]
    avg_organic_matter_pct: Optional[float]


class SoilNutrientsOut(BaseModel):
    field_id: int
    window_months: int
    months: List[SoilNutrientMonthOut]
    nitrogen_trend: str          # improving | stable | declining
    phosphorus_trend: str
    potassium_trend: str
    organic_matter_trend: str
