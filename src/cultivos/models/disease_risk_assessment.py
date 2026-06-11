"""Pydantic models for the disease outbreak risk assessment endpoint."""

from pydantic import BaseModel


class AtRiskDisease(BaseModel):
    name_es: str                # Spanish name
    name_en: str                # English common name (Latin binomial preserved)
    probability: float          # 0.0-1.0
    preventive_action: str      # Spanish preventive recommendation
    action_en: str              # English preventive recommendation


class DiseaseRiskAssessmentOut(BaseModel):
    risk_level: str             # low | medium | high
    risk_score: float           # 0-100
    at_risk_diseases: list[AtRiskDisease]
    assessment_date: str        # ISO date string
