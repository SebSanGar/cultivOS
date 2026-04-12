"""Pydantic models for cooperative disease outbreak risk aggregate endpoint."""

from pydantic import BaseModel


class OutbreakFarmDetail(BaseModel):
    farm_id: int
    farm_name: str
    high_risk_fields: int
    medium_risk_fields: int
    low_risk_fields: int
    total_fields: int


class CoopOutbreakRiskOut(BaseModel):
    cooperative_id: int
    total_high_risk_fields: int
    total_medium_risk_fields: int
    total_low_risk_fields: int
    top_risk_crop: str | None
    affected_farms_count: int
    overall_risk_level: str  # high | medium | low
    farms: list[OutbreakFarmDetail]
