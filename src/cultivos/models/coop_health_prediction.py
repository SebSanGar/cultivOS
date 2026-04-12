"""Pydantic schemas for cooperative 30-day health prediction aggregate."""

from pydantic import BaseModel


class CoopHealthTrendDistribution(BaseModel):
    improving: int
    stable: int
    declining: int


class CoopHealthTopDecliningFarm(BaseModel):
    farm_id: int
    farm_name: str
    delta: float


class CoopHealthFarmEntry(BaseModel):
    farm_id: int
    farm_name: str
    fields_count: int
    fields_with_data: int
    avg_current_health: float
    avg_predicted_30d: float
    fields_at_risk: int
    trend: str


class CoopHealthPredictionOut(BaseModel):
    cooperative_id: int
    fields_count: int
    fields_with_data: int
    avg_current_health: float
    avg_predicted_health_30d: float
    projected_delta: float
    fields_at_risk_count: int
    trend_distribution: CoopHealthTrendDistribution
    top_declining_farm: CoopHealthTopDecliningFarm | None
    farms: list[CoopHealthFarmEntry]
