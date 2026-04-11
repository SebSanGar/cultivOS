"""Pydantic models for cooperative carbon sequestration summary."""

from pydantic import BaseModel


class CoopCarbonSummaryOut(BaseModel):
    cooperative_id: int
    total_co2e_baseline_t: float
    total_projected_5yr_t: float
    avg_confidence: str  # high | medium | low
    fields_with_data_count: int
    fields_total_count: int
