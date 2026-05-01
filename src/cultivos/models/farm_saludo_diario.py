"""Pydantic response model for farm daily Spanish greeting endpoint."""

from typing import Optional

from pydantic import BaseModel, Field


class SaludoDiarioOut(BaseModel):
    """Two-sentence Spanish greeting — WhatsApp paste-ready."""

    farm_name: str = Field(..., description="Farm display name")
    weather_es: str = Field(..., description="Spanish weather sentence")
    open_alerts: int = Field(..., description="Unacknowledged alert count")
    urgent_field: Optional[str] = Field(None, description="Most urgent field name")
    saludo_es: str = Field(..., description="Two-sentence Spanish greeting, max 200 chars")
