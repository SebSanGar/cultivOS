"""Pydantic schemas for soil amendment calculator."""

from pydantic import BaseModel, Field


class SoilAmendmentRequest(BaseModel):
    current_ph: float = Field(..., ge=0, le=14)
    target_ph: float = Field(6.5, ge=0, le=14)
    current_om_pct: float = Field(..., ge=0, le=100)
    target_om_pct: float = Field(4.0, ge=0, le=100)
    current_n_ppm: float = Field(..., ge=0)
    target_n_ppm: float = Field(40.0, ge=0)
    current_p_ppm: float = Field(..., ge=0)
    target_p_ppm: float = Field(25.0, ge=0)
    current_k_ppm: float = Field(..., ge=0)
    target_k_ppm: float = Field(200.0, ge=0)


class AmendmentItem(BaseModel):
    name: str
    kg_per_ha: float
    reason_es: str
    cost_mxn_per_ha: float
    organic: bool = True


class SoilAmendmentResponse(BaseModel):
    amendments: list[AmendmentItem]
    summary_es: str
    total_cost_mxn_per_ha: float
