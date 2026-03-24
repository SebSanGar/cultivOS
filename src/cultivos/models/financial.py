"""Pydantic schemas for menu engineering and financial analysis."""

from decimal import Decimal

from pydantic import BaseModel


class MenuEngineeringItem(BaseModel):
    recipe_id: int
    recipe_name: str
    food_cost: Decimal
    menu_price: Decimal | None = None
    margin: Decimal | None = None
    popularity: int  # units sold or production count
    classification: str  # star, puzzle, plowhorse, dog


class MenuEngineeringMatrix(BaseModel):
    location_id: int
    items: list[MenuEngineeringItem]
    avg_margin: Decimal
    avg_popularity: Decimal
    stars: int
    puzzles: int
    plowhorses: int
    dogs: int


class FoodCostSummary(BaseModel):
    location_id: int
    total_food_cost: Decimal
    total_revenue: Decimal | None = None
    food_cost_percentage: Decimal | None = None
