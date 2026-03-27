"""Pydantic schemas for Treatment endpoints."""

from datetime import datetime
from typing import Optional

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
    ancestral_method_name: Optional[str] = None
    ancestral_base_cientifica: Optional[str] = None
    ancestral_razon_match: Optional[str] = None
    applied_at: Optional[datetime] = None
    applied_notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TreatmentAppliedIn(BaseModel):
    applied_at: datetime
    notes: Optional[str] = None


class TreatmentEffectivenessOut(BaseModel):
    treatment_id: int
    problema: str
    tratamiento: str
    applied_at: Optional[datetime] = None
    score_before: Optional[float] = None
    score_after: Optional[float] = None
    delta: Optional[float] = None
    status: str  # "effective", "ineffective", "neutral", "insufficient_data", "not_applied"


class TreatmentTimelineEntry(BaseModel):
    treatment_id: int
    problema: str
    tratamiento: str
    urgencia: str
    applied_at: Optional[datetime] = None
    applied_notes: Optional[str] = None
    health_score_used: float
    created_at: datetime

    model_config = {"from_attributes": True}
