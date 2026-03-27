"""Pydantic schemas for drone flight logs."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FlightLogCreate(BaseModel):
    drone_type: str = Field(..., description="mavic_multispectral, mavic_thermal, agras_t100")
    mission_type: str = Field(default="health_scan", description="health_scan, thermal_check, spray")
    flight_date: datetime
    duration_minutes: float = Field(..., gt=0)
    altitude_m: float = Field(..., gt=0)
    images_count: int = Field(default=0, ge=0)
    coverage_pct: float = Field(default=0, ge=0, le=100)
    s3_path: Optional[str] = None


class FlightLogOut(BaseModel):
    id: int
    field_id: int
    drone_type: str
    mission_type: str
    flight_date: datetime
    duration_minutes: float
    altitude_m: float
    images_count: int
    coverage_pct: float
    s3_path: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FlightStatsOut(BaseModel):
    total_flights: int
    total_hours: float
    total_area_covered_ha: float
    drone_breakdown: dict[str, int]
