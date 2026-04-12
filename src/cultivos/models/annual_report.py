"""Pydantic response model for GET /api/farms/{farm_id}/annual-report."""

from typing import Optional

from pydantic import BaseModel


class FieldAnnualItem(BaseModel):
    field_id: int
    field_name: str
    avg_health: Optional[float]
    min_health: Optional[float]
    max_health: Optional[float]
    ndvi_trend: Optional[float]
    soil_ph_delta: Optional[float]
    treatments_applied: int
    regen_score: Optional[float]


class AnnualReportOut(BaseModel):
    farm_id: int
    year: int
    fields: list[FieldAnnualItem]
    best_field: Optional[str]
    most_improved_field: Optional[str]
    total_co2e_sequestered_t: float
    treatments_applied_total: int
