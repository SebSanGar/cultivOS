"""Pydantic models for fertilizer-for-stress endpoint."""

from pydantic import BaseModel


class FertilizerRecommendation(BaseModel):
    fertilizer_name: str
    why_now_es: str
    application_es: str


class FertilizerStressOut(BaseModel):
    field_id: int
    crop_type: str
    stress_level: str
    recommendations: list[FertilizerRecommendation]


class FertilizerStressNoUrgency(BaseModel):
    message_es: str
