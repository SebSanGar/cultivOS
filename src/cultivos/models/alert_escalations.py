"""Pydantic models for farm alert escalation backlog."""

from pydantic import BaseModel


class AlertEscalationItem(BaseModel):
    alert_id: int
    field_id: int
    field_name: str
    alert_type: str
    message: str
    days_pending: int
    severity: str
    recommended_action_es: str


class FarmAlertEscalationsOut(BaseModel):
    farm_id: int
    days: int
    total: int
    escalations: list[AlertEscalationItem]
