"""Pydantic schemas for production scheduling, par levels, and demand."""

from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Par levels
# ---------------------------------------------------------------------------

class ParLevelCreate(BaseModel):
    recipe_id: int
    location_id: int
    base_par: int = Field(ge=0)
    safety_buffer: int = Field(ge=0, default=0)


class ParLevelRead(BaseModel):
    id: int
    recipe_id: int
    location_id: int
    base_par: int
    safety_buffer: int
    effective_par: int
    review_frequency: str
    last_reviewed: datetime | None
    auto_adjusted: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ParLevelRecommendation(BaseModel):
    recipe_id: int
    avg_demand: Decimal
    demand_stddev: Decimal
    recommended_base_par: int
    recommended_safety_buffer: int
    recommended_effective_par: int


# ---------------------------------------------------------------------------
# Production calendar
# ---------------------------------------------------------------------------

class ProductionCalendarCreate(BaseModel):
    location_id: int
    week_start_date: datetime


class ProductionCalendarRead(BaseModel):
    id: int
    location_id: int
    week_start_date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductionCalendarDetail(ProductionCalendarRead):
    entries: list["ProductionEntryRead"] = []


# ---------------------------------------------------------------------------
# Production entry
# ---------------------------------------------------------------------------

class ProductionEntryCreate(BaseModel):
    recipe_id: int
    planned_quantity: int = Field(ge=0)
    scheduled_date: datetime
    slot: str | None = None
    assigned_to: int | None = None
    notes: str | None = None


class ProductionEntryUpdate(BaseModel):
    status: str | None = None  # planned, in_progress, completed, cancelled
    actual_quantity: int | None = None
    notes: str | None = None


class ProductionEntryRead(BaseModel):
    id: int
    calendar_id: int
    recipe_id: int
    planned_quantity: int
    actual_quantity: int | None
    scheduled_date: datetime
    slot: str | None
    assigned_to: int | None
    status: str
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Production needs (computed)
# ---------------------------------------------------------------------------

class ProductionNeed(BaseModel):
    recipe_id: int
    recipe_name: str | None = None
    effective_par: int
    current_stock: int
    needed: int
