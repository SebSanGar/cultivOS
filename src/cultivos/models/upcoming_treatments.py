"""Pydantic schema for per-field upcoming treatment schedule."""

from pydantic import BaseModel


class UpcomingTreatmentOut(BaseModel):
    treatment_type: str     # e.g. "fertilizacion", "riego", "control_plagas"
    recommended_date: str   # ISO date string YYYY-MM-DD
    reason_es: str          # Spanish explanation for the recommendation
