"""Pydantic response model for field Spanish plain-language summary endpoint."""

from pydantic import BaseModel, Field


class FieldResumenOut(BaseModel):
    """Spanish plain-language 3-sentence summary of a single field's state."""

    field_name: str = Field(..., description="Field display name")
    health_status: str = Field(..., description="bueno | regular | malo | sin_datos")
    urgency: str = Field(..., description="ninguna | baja | media | alta")
    summary_es: str = Field(..., description="3-sentence farmer-friendly Spanish summary")
