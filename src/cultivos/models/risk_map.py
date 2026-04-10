"""Pydantic models for field risk heatmap."""

from __future__ import annotations

from pydantic import BaseModel


class FieldRiskItem(BaseModel):
    """Risk assessment for a single field — used in the farm risk map response."""

    field_id: int
    name: str
    lat: float | None
    lon: float | None
    risk_score: float | None  # 0-100; null when no data exists
    dominant_factor: str | None  # "health" | "weather" | "disease" | "thermal"; null when no data


class FarmRiskMapOut(BaseModel):
    """Response model for GET /api/farms/{farm_id}/fields/risk-map."""

    farm_id: int
    fields: list[FieldRiskItem]
