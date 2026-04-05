"""Pydantic schemas for farmer feedback endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class FeedbackIn(BaseModel):
    treatment_id: int
    rating: int  # 1-5
    worked: bool
    farmer_notes: Optional[str] = None
    alternative_method: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class FeedbackOut(BaseModel):
    id: int
    field_id: int
    treatment_id: int
    rating: int
    worked: bool
    farmer_notes: Optional[str] = None
    alternative_method: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TreatmentTrustItem(BaseModel):
    treatment_name: str
    total_feedback: int
    positive_count: int
    negative_count: int
    average_rating: float
    trust_score: float  # 0-100 weighted score
    top_farmer_note: Optional[str] = None


class TreatmentTrustOut(BaseModel):
    treatments: list[TreatmentTrustItem]


class TEKMethodValidation(BaseModel):
    method_name: str
    total_feedback: int
    positive_count: int
    negative_count: int
    average_rating: float
    trust_score: float  # 0-100 weighted score


class TEKValidationOut(BaseModel):
    methods: list[TEKMethodValidation]
