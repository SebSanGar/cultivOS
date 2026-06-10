"""Pydantic schemas for economic impact endpoints."""

from typing import List, Literal, Optional

from pydantic import BaseModel


class EconomicImpactOut(BaseModel):
    farm_id: int
    hectares: float
    water_savings_mxn: int
    fertilizer_savings_mxn: int
    yield_improvement_mxn: int
    total_savings_mxn: int
    total_savings_low_mxn: int
    total_savings_high_mxn: int
    confidence: Literal["low", "medium", "high"]
    confidence_label: Literal["Estimado", "Medido", "Confirmado"]
    is_estimate: bool
    basis: List[str]
    subscription_cost_mxn: Optional[int] = None
    net_savings_mxn: Optional[int] = None
    roi_multiple: Optional[float] = None
    payback_months: Optional[int] = None
    savings_per_ha_mxn: Optional[int] = None
    water_savings_per_ha_mxn: Optional[int] = None
    fertilizer_savings_per_ha_mxn: Optional[int] = None
    yield_improvement_per_ha_mxn: Optional[int] = None
    # T2.4 — three-scenario chart: 100%-efficiency ceiling per category
    water_potential_mxn: Optional[int] = None
    fertilizer_potential_mxn: Optional[int] = None
    yield_potential_mxn: Optional[int] = None
    nota: str
