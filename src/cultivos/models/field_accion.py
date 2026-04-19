"""Pydantic response model for field one-sentence Spanish next-action endpoint."""

from pydantic import BaseModel, Field


class FieldAccionOut(BaseModel):
    """One-sentence Spanish next-action for a single field — WhatsApp-sized."""

    field_name: str = Field(..., description="Field display name")
    priority: str = Field(..., description="alta | media | baja | ninguna")
    source: str = Field(..., description="alert | treatment | health | monitoring")
    accion_es: str = Field(..., description="Single Spanish sentence ending with '.'")
