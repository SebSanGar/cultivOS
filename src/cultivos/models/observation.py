"""Pydantic models for farmer observation endpoints."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


ObservationType = Literal["problem", "success", "neutral"]


class FarmerObservationIn(BaseModel):
    observation_es: str
    observation_type: ObservationType
    crop_stage: Optional[str] = None


class FarmerObservationOut(BaseModel):
    id: int
    field_id: int
    observation_es: str
    observation_type: str
    crop_stage: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FarmerObservationListOut(BaseModel):
    field_id: int
    total: int
    items: List[FarmerObservationOut]
