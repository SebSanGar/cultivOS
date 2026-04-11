"""Pydantic response model for GET /api/farms/{farm_id}/fields/{field_id}/timeline."""

from typing import Optional
from pydantic import BaseModel


class TimelineEvent(BaseModel):
    event_type: str          # health_score | ndvi | treatment | alert
    date: str                # ISO 8601 datetime string
    summary_es: str          # Spanish-language summary
    value: Optional[float]   # numeric value (score, ndvi_mean, cost_mxn) or None


class FieldTimelineOut(BaseModel):
    field_id: int
    events: list[TimelineEvent]
