"""Pydantic response models for field disease history endpoint (#204)."""

from typing import Optional

from pydantic import BaseModel


class DiseaseHistoryMonth(BaseModel):
    month: str
    triggers: list[str]
    diseases: list[str]
    disease_count: int


class FieldDiseaseHistoryOut(BaseModel):
    farm_id: int
    field_id: int
    months: int
    total_months_analyzed: int
    monthly: list[DiseaseHistoryMonth]
    disease_counts: dict[str, int]
    most_common_disease: Optional[str]
    recurring_diseases: list[str]
    recurrence_detected: bool
    months_disease_free: int
