"""Pydantic schema for cooperative portfolio health endpoint."""

from pydantic import BaseModel


class CooperativePortfolioOut(BaseModel):
    cooperative_id: int
    name: str
    total_farms: int
    total_fields: int
    total_hectares: float
    avg_health_score: float | None
    fields_needing_attention: int
    total_co2e_sequestered: float
    economic_impact_mxn: int
