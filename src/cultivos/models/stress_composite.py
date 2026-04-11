"""Pydantic response model for field crop stress composite index."""

from pydantic import BaseModel


class StressComponentsOut(BaseModel):
    water: float   # 0-100 normalized water stress component
    disease: float  # 0-100 disease risk score
    thermal: float  # 0-100 thermal stress percentage


class StressCompositeOut(BaseModel):
    field_id: int
    stress_index: float        # 0-100 composite
    stress_level: str          # none | low | moderate | high | critical
    components: StressComponentsOut
    recommendation_es: str
