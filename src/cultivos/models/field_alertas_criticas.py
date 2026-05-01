"""Pydantic response models for field critical alerts endpoint."""

from pydantic import BaseModel, Field


class AlertaCriticaItem(BaseModel):
    alert_id: int = Field(..., description="AlertLog row ID")
    severity: str = Field(..., description="critical or high")
    mensaje_es: str = Field(..., description="One Spanish sentence describing the alert")


class AlertasCriticasOut(BaseModel):
    field_name: str = Field(..., description="Field display name")
    total: int = Field(..., description="Number of open critical/high alerts")
    alertas: list[AlertaCriticaItem] = Field(default_factory=list)
