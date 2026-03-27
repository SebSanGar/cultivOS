"""Pydantic schemas for soil microbiome indicator endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class MicrobiomeCreate(BaseModel):
    respiration_rate: float = Field(..., ge=0, description="mg CO2/kg/day")
    microbial_biomass_carbon: float = Field(..., ge=0, description="mg C/kg soil")
    fungi_bacteria_ratio: float = Field(..., ge=0)
    sampled_at: datetime


class MicrobiomeOut(BaseModel):
    id: int
    field_id: int
    respiration_rate: float
    microbial_biomass_carbon: float
    fungi_bacteria_ratio: float
    classification: str
    sampled_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


def classify_microbiome(respiration_rate: float) -> str:
    """Classify microbiome health based on soil respiration rate (mg CO2/kg/day).

    >50 = healthy, 20-50 = moderate, <20 = degraded.
    """
    if respiration_rate > 50:
        return "healthy"
    elif respiration_rate >= 20:
        return "moderate"
    return "degraded"
