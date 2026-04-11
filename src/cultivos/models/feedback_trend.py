"""Pydantic response models for farmer feedback trend endpoint."""

from pydantic import BaseModel


class FeedbackMonthItem(BaseModel):
    month_label: str   # "YYYY-MM"
    avg_rating: float
    entry_count: int


class FeedbackTrendOut(BaseModel):
    farm_id: int
    months: list[FeedbackMonthItem]
    overall_trend: str  # "improving" | "stable" | "declining"
