"""Pydantic models for organic certification readiness endpoint."""

from pydantic import BaseModel


class CertificationReadinessOut(BaseModel):
    synthetic_inputs_free: bool
    treatment_organic_only: bool
    soc_trend_positive: bool
    cover_crop_days_gte_90: bool
    overall_pct: float
