"""Pydantic schemas for Alert Configuration API."""

from datetime import datetime

from pydantic import BaseModel, Field


class AlertConfigCreate(BaseModel):
    health_score_floor: float = Field(default=40.0, ge=0, le=100)
    ndvi_minimum: float = Field(default=0.3, ge=0.0, le=1.0)
    temp_max_c: float = Field(default=45.0, ge=-50, le=70)


class AlertConfigUpdate(BaseModel):
    health_score_floor: float | None = Field(default=None, ge=0, le=100)
    ndvi_minimum: float | None = Field(default=None, ge=0.0, le=1.0)
    temp_max_c: float | None = Field(default=None, ge=-50, le=70)


class AlertConfigOut(BaseModel):
    id: int
    farm_id: int
    health_score_floor: float
    ndvi_minimum: float
    temp_max_c: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
