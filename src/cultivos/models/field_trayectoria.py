"""Pydantic response model for field 7-day Spanish trajectory endpoint."""

from typing import Optional

from pydantic import BaseModel, Field


class FieldTrayectoriaOut(BaseModel):
    """7-day health trajectory for a single field — WhatsApp-sized Spanish summary."""

    field_name: str = Field(..., description="Field display name")
    days_window: int = Field(default=7, description="Lookback window in days")
    health_delta: Optional[float] = Field(None, description="latest_score - oldest_score in window; None if <2 scores")
    alerts_count: int = Field(..., description="AlertLog count where created_at in last 7 days")
    treatments_count: int = Field(..., description="TreatmentRecord count where applied_at in last 7 days")
    trend: str = Field(..., description="mejorando | estable | empeorando | sin_datos")
    narrativa_es: str = Field(..., description="1-2 sentence Spanish summary, <=200 chars")
