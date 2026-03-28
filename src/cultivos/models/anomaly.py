"""Pydantic schemas for field-level anomaly detection."""

from pydantic import BaseModel


class HealthAnomalyOut(BaseModel):
    type: str
    field_name: str
    drop: float
    previous_score: float
    current_score: float
    recommendation: str


class NDVIAnomalyOut(BaseModel):
    type: str
    field_name: str
    current_ndvi: float
    historical_avg: float
    drop_pct: float
    recommendation: str


class FieldAnomaliesOut(BaseModel):
    field_id: int
    field_name: str
    health_anomalies: list[HealthAnomalyOut]
    ndvi_anomalies: list[NDVIAnomalyOut]
