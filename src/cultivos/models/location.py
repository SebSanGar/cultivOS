"""Pydantic schemas for locations and users."""

from datetime import datetime

from pydantic import BaseModel


class LocationCreate(BaseModel):
    name: str
    address: str | None = None
    timezone: str = "America/Toronto"
    currency: str = "CAD"


class LocationRead(BaseModel):
    id: int
    name: str
    address: str | None
    timezone: str
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}
