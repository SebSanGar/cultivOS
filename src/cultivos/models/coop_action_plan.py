"""Pydantic models for GET /api/cooperatives/{coop_id}/action-plan."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class CoopActionItem(BaseModel):
    farm_id: int
    farm_name: str
    field_id: int
    crop_type: str | None
    priority: Literal["high", "medium", "low"]
    category: Literal["stress", "treatment", "tek"]
    action_es: str
    source_es: str


class CoopActionPlanOut(BaseModel):
    cooperative_id: int
    period_days: int
    total_fields_scanned: int
    total_actions: int
    high_count: int
    medium_count: int
    low_count: int
    actions: list[CoopActionItem]
