"""Pydantic schema for multi-field health comparison endpoint."""

from typing import Optional
from pydantic import BaseModel


class FieldComparisonItem(BaseModel):
    field_id: int
    field_name: str
    latest_health: Optional[float]
    latest_ndvi: Optional[float]
    latest_soil_ph: Optional[float]
    trend: Optional[str]  # improving | stable | declining | None
