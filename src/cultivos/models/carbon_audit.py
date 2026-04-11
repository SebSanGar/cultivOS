"""Pydantic schema for farm soil carbon audit endpoint."""

from pydantic import BaseModel


class CarbonAuditOut(BaseModel):
    farm_id: int
    total_current_co2e_t: float
    total_projected_5yr_co2e_t: float
    total_annual_seq_t_per_yr: float
    fields_with_baseline: int
    fields_without_baseline: int
    total_fields: int
