"""Pydantic response model for farm-level Spanish WhatsApp digest endpoint."""

from pydantic import BaseModel, Field


class FarmDigestOut(BaseModel):
    """100-200 char Spanish digest of all fields — WhatsApp paste-ready."""

    farm_name: str = Field(..., description="Farm display name")
    field_count: int = Field(..., description="Number of fields in the farm")
    top_priority: str = Field(..., description="alta | media | baja | ninguna")
    digest_es: str = Field(..., description="Spanish digest under 200 chars")
