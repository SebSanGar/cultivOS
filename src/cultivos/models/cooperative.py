"""Pydantic schemas for Cooperative endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class CooperativeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    state: str = "Jalisco"
    contact_name: str | None = None
    contact_phone: str | None = None


class CooperativeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    state: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None


class CooperativeOut(BaseModel):
    id: int
    name: str
    state: str
    contact_name: str | None
    contact_phone: str | None
    farm_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class CooperativeFarmSummary(BaseModel):
    id: int
    name: str
    total_hectares: float
    field_count: int = 0
    avg_health: float | None = None


class CooperativeDashboard(BaseModel):
    cooperative_id: int
    cooperative_name: str
    total_farms: int = 0
    total_fields: int = 0
    total_hectares: float = 0
    avg_health: float | None = None
    farms: list[CooperativeFarmSummary] = []
