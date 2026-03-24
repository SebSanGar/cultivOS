"""Pydantic schemas for suppliers and ingredient pricing."""

from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------

class SupplierCreate(BaseModel):
    name: str
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    categories: list[str] = []
    payment_terms: str | None = None
    minimum_order: Decimal | None = None
    location_id: int


class SupplierRead(BaseModel):
    id: int
    name: str
    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None
    address: str | None
    categories: list[str]
    reliability_score: Decimal | None
    quality_rating: Decimal | None
    price_competitiveness: Decimal | None
    payment_terms: str | None
    minimum_order: Decimal | None
    relationship_status: str
    location_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Ingredient price
# ---------------------------------------------------------------------------

class IngredientPriceCreate(BaseModel):
    ingredient_id: int
    supplier_id: int
    price_per_unit: Decimal = Field(gt=0)
    unit: str = "kg"
    quoted_price: Decimal | None = None
    invoice_price: Decimal | None = None
    volume_tier: str | None = None
    delivery_terms: str | None = None
    notes: str | None = None


class IngredientPriceRead(BaseModel):
    id: int
    ingredient_id: int
    supplier_id: int
    price_per_unit: Decimal
    unit: str
    effective_date: datetime
    quoted_price: Decimal | None
    invoice_price: Decimal | None
    volume_tier: str | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Price comparison
# ---------------------------------------------------------------------------

class PriceComparison(BaseModel):
    ingredient_id: int
    ingredient_name: str | None = None
    prices: list["SupplierPrice"]


class SupplierPrice(BaseModel):
    supplier_id: int
    supplier_name: str
    price_per_unit: Decimal
    unit: str
    effective_date: datetime
