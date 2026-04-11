"""Pydantic models for seasonal performance benchmark endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class SeasonalFieldBenchmark(BaseModel):
    field_id: int
    field_name: str
    current_avg: float | None
    prior_avg: float | None
    delta: float | None
    improved: bool | None


class SeasonalBenchmarkOut(BaseModel):
    current_season: str
    prior_season: str
    fields: list[SeasonalFieldBenchmark]
    overall_trend: str  # "improving" | "declining" | "stable"
