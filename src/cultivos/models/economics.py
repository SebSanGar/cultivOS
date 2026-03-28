"""Pydantic schemas for economic impact endpoints."""

from pydantic import BaseModel


class EconomicImpactOut(BaseModel):
    farm_id: int
    hectares: float
    water_savings_mxn: int
    fertilizer_savings_mxn: int
    yield_improvement_mxn: int
    total_savings_mxn: int
    nota: str
