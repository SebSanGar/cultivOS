"""Pydantic schemas for recipes, ingredients, and scaling."""

from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Ingredient
# ---------------------------------------------------------------------------

class IngredientCreate(BaseModel):
    name: str
    category: str | None = None
    default_unit: str = "g"
    location_id: int


class IngredientRead(BaseModel):
    id: int
    name: str
    category: str | None
    default_unit: str
    location_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Recipe
# ---------------------------------------------------------------------------

class RecipeCreate(BaseModel):
    name: str
    category: str | None = None
    location_id: int
    base_yield: int = Field(ge=1)
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    total_time_minutes: int | None = None
    shelf_life_hours: int | None = None
    allergens: list[str] = []
    tags: list[str] = []


class RecipeUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    base_yield: int | None = Field(default=None, ge=1)
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    total_time_minutes: int | None = None
    shelf_life_hours: int | None = None
    allergens: list[str] | None = None
    tags: list[str] | None = None


class RecipeRead(BaseModel):
    id: int
    name: str
    category: str | None
    location_id: int
    base_yield: int
    prep_time_minutes: int | None
    cook_time_minutes: int | None
    total_time_minutes: int | None
    shelf_life_hours: int | None
    allergens: list[str]
    tags: list[str]
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# RecipeIngredient
# ---------------------------------------------------------------------------

class RecipeIngredientCreate(BaseModel):
    ingredient_id: int
    amount: Decimal = Field(gt=0)
    unit: str = "g"
    scaling_type: str = "linear"


class RecipeIngredientRead(BaseModel):
    id: int
    recipe_id: int
    ingredient_id: int
    ingredient_name: str | None = None
    amount: Decimal
    unit: str
    scaling_type: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# RecipeStep
# ---------------------------------------------------------------------------

class RecipeStepCreate(BaseModel):
    step_order: int
    instruction: str
    time_minutes: int | None = None
    temperature_c: int | None = None


class RecipeStepRead(BaseModel):
    id: int
    recipe_id: int
    step_order: int
    instruction: str
    time_minutes: int | None
    temperature_c: int | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# ScalingRule
# ---------------------------------------------------------------------------

class ScalingRuleCreate(BaseModel):
    ingredient_id: int
    rule_type: str = "linear"
    exponent: Decimal = Decimal("1.0")
    step_size: Decimal | None = None
    custom_curve_json: str | None = None


class ScalingRuleRead(BaseModel):
    id: int
    recipe_id: int
    ingredient_id: int
    rule_type: str
    exponent: Decimal
    step_size: Decimal | None
    custom_curve_json: str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Recipe detail (nested)
# ---------------------------------------------------------------------------

class RecipeDetail(RecipeRead):
    ingredients: list[RecipeIngredientRead] = []
    steps: list[RecipeStepRead] = []
    scaling_rules: list[ScalingRuleRead] = []


# ---------------------------------------------------------------------------
# Scaling output
# ---------------------------------------------------------------------------

class ScaledIngredient(BaseModel):
    ingredient_id: int
    ingredient_name: str | None = None
    base_amount: Decimal
    scaled_amount: Decimal
    unit: str
    scaling_type: str


class ScaledRecipeResponse(BaseModel):
    recipe_id: int
    recipe_name: str
    base_yield: int
    target_yield: int
    scale_factor: Decimal
    ingredients: list[ScaledIngredient]
    cost_per_portion: Decimal | None = None


# ---------------------------------------------------------------------------
# Cost
# ---------------------------------------------------------------------------

class CostBreakdown(BaseModel):
    recipe_id: int
    recipe_name: str
    base_yield: int
    total_cost: Decimal
    cost_per_portion: Decimal
    ingredients: list["IngredientCostLine"]


class IngredientCostLine(BaseModel):
    ingredient_id: int
    ingredient_name: str | None = None
    amount: Decimal
    unit: str
    unit_cost: Decimal
    line_cost: Decimal
