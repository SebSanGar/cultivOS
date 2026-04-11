"""Pydantic models for TEK-sensor alignment response."""

from __future__ import annotations

from pydantic import BaseModel


class PracticeAlignmentItem(BaseModel):
    name: str
    timing_rationale: str | None
    sensor_support: bool
    evidence_es: str


class SensorContext(BaseModel):
    water_stress_level: str
    disease_risk_level: str
    thermal_stress_pct: float


class TekAlignmentOut(BaseModel):
    field_id: int
    month: int
    crop_type: str
    alignment_score_pct: float
    sensor_context: SensorContext
    practices: list[PracticeAlignmentItem]
