"""Pydantic model for health score volatility response."""

from __future__ import annotations

from pydantic import BaseModel


class HealthVolatilityOut(BaseModel):
    field_id: int
    period_days: int
    score_count: int
    mean_health: float | None
    std_dev: float | None
    volatility_tier: str  # stable / moderate / volatile / insufficient_data
    interpretation_es: str
