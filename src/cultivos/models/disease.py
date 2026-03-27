"""Pydantic schemas for disease/pest identification."""

from pydantic import BaseModel


class TreatmentInfo(BaseModel):
    name: str
    description_es: str
    organic: bool = True

    model_config = {"from_attributes": True}


class DiseaseOut(BaseModel):
    id: int
    name: str
    description_es: str
    symptoms: list[str]
    affected_crops: list[str]
    treatments: list[TreatmentInfo]
    region: str
    severity: str

    model_config = {"from_attributes": True}


class DiseaseMatch(BaseModel):
    """Result of symptom-based disease identification."""
    id: int
    name: str
    description_es: str
    symptoms: list[str]
    affected_crops: list[str]
    treatments: list[TreatmentInfo]
    region: str
    severity: str
    confidence: float  # 0.0-1.0 based on symptom overlap
    symptoms_matched: list[str]

    model_config = {"from_attributes": True}


class IdentifyRequest(BaseModel):
    symptoms: list[str]
    crop: str | None = None


class RiskItemOut(BaseModel):
    tipo: str
    descripcion: str
    recomendacion: str
    urgencia: str
    organico: bool


class DiseaseRiskOut(BaseModel):
    field_id: int
    risk_level: str
    mensaje: str
    risks: list[RiskItemOut]
    nota: str | None = None
