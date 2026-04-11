"""Pydantic models for the field stress report endpoint."""

from pydantic import BaseModel


class StressFactor(BaseModel):
    source: str        # health | ndvi | thermal | soil
    metric: str        # specific metric name
    value: float       # observed value
    impact: int        # points added to stress score


class FieldStressReportOut(BaseModel):
    field_id: int
    field_name: str
    stress_score: float          # 0-100
    stress_level: str            # low | medium | high | critical
    contributing_factors: list[StressFactor]
    recommended_priority: int    # 1 (low) to 5 (critical)
