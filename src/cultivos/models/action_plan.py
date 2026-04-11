"""Pydantic models for GET /api/farms/{farm_id}/fields/{field_id}/action-plan."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ActionItem(BaseModel):
    priority: Literal["high", "medium", "low"]
    category: Literal["stress", "treatment", "tek"]
    action_es: str
    source_es: str


class ActionPlanOut(BaseModel):
    field_id: int
    crop_type: str | None
    period_days: int
    actions: list[ActionItem]
