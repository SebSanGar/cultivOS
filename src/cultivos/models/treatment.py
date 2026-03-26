"""Pydantic schemas for Treatment endpoints."""

from datetime import datetime

from pydantic import BaseModel


class TreatmentOut(BaseModel):
    id: int
    field_id: int
    health_score_used: float
    problema: str
    causa_probable: str
    tratamiento: str
    costo_estimado_mxn: int
    urgencia: str
    prevencion: str
    organic: bool
    created_at: datetime

    model_config = {"from_attributes": True}
