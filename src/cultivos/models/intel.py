"""Pydantic models for intelligence dashboard API."""

from pydantic import BaseModel
from typing import Optional


class WorstField(BaseModel):
    field_id: int
    field_name: str
    farm_name: str
    score: float


class IntelSummaryOut(BaseModel):
    total_farms: int
    total_fields: int
    avg_health: Optional[float] = None
    worst_field: Optional[WorstField] = None


class SoilTrendEntry(BaseModel):
    date: str
    avg_ph: float
    avg_organic_matter: float
    sample_count: int


class SoilTrendsOut(BaseModel):
    trends: list[SoilTrendEntry]


class TreatmentEffectivenessEntry(BaseModel):
    field_name: str
    farm_name: str
    tratamiento: str
    health_before: float
    health_after: Optional[float] = None
    delta: Optional[float] = None
    urgencia: str
    organic: bool


class TreatmentEffectivenessOut(BaseModel):
    treatments: list[TreatmentEffectivenessEntry]


class AnomalyEntry(BaseModel):
    field_id: int
    field_name: str
    farm_name: str
    consecutive_declines: int
    latest_score: float
    score_history: list[float]


class AnomaliesOut(BaseModel):
    anomalies: list[AnomalyEntry]
