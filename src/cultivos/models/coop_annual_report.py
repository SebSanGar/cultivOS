"""Pydantic models for cooperative annual report aggregate."""

from typing import Optional

from pydantic import BaseModel


class BestFarmEntry(BaseModel):
    farm_id: int
    farm_name: str
    health_delta: float


class CoopAnnualReportOut(BaseModel):
    cooperative_id: int
    year: int
    total_farms: int
    total_fields: int
    avg_health_change: float
    total_co2e_sequestered_t: float
    total_treatments_applied: int
    best_farm: Optional[BestFarmEntry]
    farms_improved_count: int
    farms_total: int
