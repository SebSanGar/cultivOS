"""Pydantic schema for the field NDVI-health correlation endpoint (#212)."""

from __future__ import annotations

from pydantic import BaseModel


class NdviHealthCorrelationOut(BaseModel):
    field_id: int
    period_days: int
    sample_size: int
    correlation: float | None
    strength: str  # strong | moderate | weak | none | insufficient_data
    interpretation_es: str
    mean_health: float | None
    mean_ndvi: float | None
