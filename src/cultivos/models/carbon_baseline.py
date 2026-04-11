"""Pydantic models for soil carbon baseline and projection endpoints."""

from pydantic import BaseModel


class CarbonBaselineIn(BaseModel):
    soc_percent: float
    measurement_date: str   # YYYY-MM-DD
    lab_method: str


class CarbonBaselineOut(BaseModel):
    id: int
    field_id: int
    soc_percent: float
    measurement_date: str
    lab_method: str


class CarbonProjectionOut(BaseModel):
    field_id: int
    baseline_soc_pct: float
    hectares: float
    current_co2e_t: float
    projected_5yr_co2e_t: float
    sequestration_rate_t_per_yr: float
    confidence: str             # "high" | "medium" | "low"
