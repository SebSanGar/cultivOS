"""Pydantic schemas for field photo analysis."""

from datetime import datetime
from pydantic import BaseModel


class PhotoAnalysis(BaseModel):
    dominant_colors: list[dict]  # [{"color": [r,g,b], "percentage": float}]
    avg_brightness: float
    green_ratio: float
    classification: str  # healthy_vegetation, stressed_vegetation, bare_soil, mixed


class PhotoOut(BaseModel):
    id: int
    field_id: int
    filename: str
    content_type: str
    size_bytes: int | None
    uploaded_at: datetime
    analysis: PhotoAnalysis | None

    model_config = {"from_attributes": True}
