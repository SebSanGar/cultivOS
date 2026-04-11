"""Pydantic models for harvest record endpoints."""

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel


class HarvestRecordIn(BaseModel):
    crop_type: str
    harvest_date: date
    actual_yield_kg: float
    notes: Optional[str] = None


class HarvestRecordOut(BaseModel):
    id: int
    field_id: int
    crop_type: str
    harvest_date: datetime
    actual_yield_kg: float
    notes: Optional[str] = None
    predicted_vs_actual_kg: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}
