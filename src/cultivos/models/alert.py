"""Pydantic schemas for Alert endpoints."""

from datetime import datetime

from pydantic import BaseModel


class AlertOut(BaseModel):
    id: int
    farm_id: int
    field_id: int
    alert_type: str
    message: str
    phone_number: str | None
    status: str
    sent_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertCheckResponse(BaseModel):
    farm_id: int
    alerts_created: list[AlertOut]
    fields_checked: int
