"""Pydantic models for yield prediction accuracy summary."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class FieldYieldAccuracy(BaseModel):
    field_id: int
    crop_type: str
    predictions_count: int
    avg_accuracy_pct: float
    accuracy_grade: str  # green | yellow | red


class YieldAccuracyOut(BaseModel):
    farm_id: int
    overall_accuracy_pct: Optional[float]
    accuracy_grade: Optional[str]  # green | yellow | red | None when no data
    fields: list[FieldYieldAccuracy]
