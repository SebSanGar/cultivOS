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


class AlertLogCreate(BaseModel):
    field_id: int | None = None
    alert_type: str
    message: str
    severity: str = "info"


class AlertLogOut(BaseModel):
    id: int
    farm_id: int
    field_id: int | None
    alert_type: str
    message: str
    severity: str
    acknowledged: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertAnalyticsOut(BaseModel):
    total_alerts: int
    total_sms: int
    total_system: int
    delivery_rate: float
    by_type: dict[str, int]
    by_severity: dict[str, int]
    by_status: dict[str, int]
    farms_reached: int
    fields_reached: int
