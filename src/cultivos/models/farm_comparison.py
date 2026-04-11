"""Pydantic models for farm comparison endpoint."""

from typing import Optional
from pydantic import BaseModel


class FarmComparisonRow(BaseModel):
    farm_id: int
    farm_name: Optional[str] = None  # None signals unknown/not-found farm
    avg_health: Optional[float] = None
    total_hectares: Optional[float] = None
    treatment_count: Optional[int] = None
    co2e_sequestered: Optional[float] = None
    organic_pct: Optional[float] = None
    certification_readiness: Optional[float] = None


class FarmComparisonOut(BaseModel):
    farms: list[FarmComparisonRow]
