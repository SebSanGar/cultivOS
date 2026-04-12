"""Pydantic models for farm-level irrigation efficiency aggregate."""

from pydantic import BaseModel


class FieldIrrigationItem(BaseModel):
    field_id: int
    field_name: str
    crop_type: str
    efficiency_pct: float
    water_stress_index: float
    optimal_irrigation_mm: float


class WorstFieldOut(BaseModel):
    field_id: int
    field_name: str
    crop_type: str
    efficiency_pct: float
    water_stress_index: float


class FarmIrrigationEfficiencyOut(BaseModel):
    farm_id: int
    total_fields: int
    avg_water_efficiency_pct: float | None
    fields_below_70pct: int
    worst_field: WorstFieldOut | None
    fields: list[FieldIrrigationItem]
