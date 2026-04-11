"""Pydantic model for farm regional benchmark response."""

from __future__ import annotations

from pydantic import BaseModel


class RegionalBenchmarkOut(BaseModel):
    farm_id: int
    farm_name: str
    state: str
    own_avg_health: float | None  # None when farm has no HealthScore records
    state_avg_health: float | None  # None when no peers have HealthScore records
    percentile_rank: float  # 0-100; own farm's rank among all farms in state
    better_than_pct: float  # % of peer farms this farm outperforms (0-100)
    peer_farm_count: int  # number of other farms in the same state
