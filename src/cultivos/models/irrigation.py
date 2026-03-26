"""Pydantic schemas for irrigation optimization endpoints."""

from pydantic import BaseModel


class IrrigationDayOut(BaseModel):
    day: int
    liters_per_ha: float
    nota: str


class IrrigationScheduleOut(BaseModel):
    field_id: int
    crop_type: str
    hectares: float
    schedule: list[IrrigationDayOut]
    liters_total_per_ha: float
    urgencia: str
    recomendacion: str
