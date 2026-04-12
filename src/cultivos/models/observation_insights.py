"""Pydantic models for #190 farmer observation insights endpoint."""

from datetime import datetime

from pydantic import BaseModel


class ObservationTypeCount(BaseModel):
    type: str
    count: int
    pct: float


class ObservationInsightsOut(BaseModel):
    farm_id: int
    period_days: int
    total_observations: int
    observations_by_type: list[ObservationTypeCount]
    last_observed_at: datetime | None
