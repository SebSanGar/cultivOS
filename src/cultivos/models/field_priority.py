"""Pydantic models for the field prioritization ranking endpoint."""

from pydantic import BaseModel


class FieldPriorityItem(BaseModel):
    field_id: int
    name: str
    crop_type: str | None
    priority_score: float       # 0-100 (higher = more urgent)
    top_issue: str              # human-readable description of primary stressor
    recommended_action: str     # Spanish-language action recommendation


class FieldPriorityOut(BaseModel):
    farm_id: int
    fields: list[FieldPriorityItem]   # sorted by priority_score DESC
