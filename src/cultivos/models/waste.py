"""Pydantic schemas for waste tracking and shelf life."""

from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Waste log
# ---------------------------------------------------------------------------

class WasteLogCreate(BaseModel):
    location_id: int
    logged_by: int | None = None
    recipe_id: int | None = None
    ingredient_id: int | None = None
    category: str  # overproduction, spoilage, trim, plate, cooking_loss, damaged
    quantity: Decimal = Field(gt=0)
    unit: str = "kg"
    cost_estimate: Decimal | None = None
    reason: str | None = None
    photo_url: str | None = None


class WasteLogRead(BaseModel):
    id: int
    location_id: int
    logged_by: int | None
    logged_at: datetime
    recipe_id: int | None
    ingredient_id: int | None
    category: str
    quantity: Decimal
    unit: str
    cost_estimate: Decimal | None
    reason: str | None
    photo_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Waste summary (computed)
# ---------------------------------------------------------------------------

class WasteSummary(BaseModel):
    location_id: int
    period: str  # daily, weekly
    start_date: datetime
    total_waste_kg: Decimal
    total_waste_cost: Decimal
    by_category: dict[str, Decimal]
    waste_rate: Decimal | None = None  # waste_cost / total_food_cost * 100


class TopWastedItem(BaseModel):
    recipe_id: int | None = None
    ingredient_id: int | None = None
    name: str | None = None
    total_quantity: Decimal
    total_cost: Decimal
    occurrences: int


class WastePattern(BaseModel):
    pattern_type: str  # day_of_week, recipe_specific, seasonal
    description: str
    confidence: str  # high, medium, low
    recommendation: str


# ---------------------------------------------------------------------------
# Shelf life tracker
# ---------------------------------------------------------------------------

class ShelfLifeCreate(BaseModel):
    recipe_id: int
    location_id: int
    produced_at: datetime | None = None
    expires_at: datetime
    quantity_produced: int = Field(ge=1)
    quantity_remaining: int | None = None


class ShelfLifeRead(BaseModel):
    id: int
    recipe_id: int
    location_id: int
    produced_at: datetime
    expires_at: datetime
    quantity_produced: int
    quantity_remaining: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ShelfLifeUpdate(BaseModel):
    quantity_remaining: int | None = None
    status: str | None = None
