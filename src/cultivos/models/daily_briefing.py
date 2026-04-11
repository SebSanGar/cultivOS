"""Pydantic response models for GET /api/farms/{farm_id}/daily-briefing."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class UrgentFieldBrief(BaseModel):
    name: str
    issue_es: str
    action_es: str


class TreatmentReminder(BaseModel):
    field_name: str
    treatment: str
    due_date: str


class DailyBriefingOut(BaseModel):
    date: str
    weather_summary_es: str
    urgent_field: Optional[UrgentFieldBrief]
    upcoming_treatments: list[TreatmentReminder]
    overall_farm_status: str  # ok | attention | urgent
