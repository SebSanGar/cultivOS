"""Pydantic models for field crop calendar event log."""

from typing import Optional

from pydantic import BaseModel


class CalendarMonthEntry(BaseModel):
    month: int
    month_name_es: str
    health_scores: int
    treatments: int
    observations: int
    tek_practices: int
    total_events: int


class FieldCalendarOut(BaseModel):
    farm_id: int
    field_id: int
    year: int
    crop_type: Optional[str] = None
    months: list[CalendarMonthEntry]
    total_events: int
    busiest_month: Optional[int] = None
