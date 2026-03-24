"""Cost calculation service — food cost per portion.

Pure functions where possible. DB access only for price lookups.
"""

from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from cultivos.db.models import IngredientPrice, Recipe, RecipeIngredient
from cultivos.models.recipe import CostBreakdown, IngredientCostLine


def get_latest_price(db: Session, ingredient_id: int) -> Decimal:
    """Get the most recent price for an ingredient (across all suppliers)."""
    price = (
        db.query(IngredientPrice)
        .filter(IngredientPrice.ingredient_id == ingredient_id)
        .order_by(IngredientPrice.effective_date.desc())
        .first()
    )
    if price:
        return Decimal(str(price.price_per_unit))
    return Decimal("0")


def recipe_cost_breakdown(db: Session, recipe_id: int) -> CostBreakdown | None:
    """Calculate detailed cost breakdown for a recipe at base yield."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        return None

    recipe_ingredients = (
        db.query(RecipeIngredient)
        .filter(RecipeIngredient.recipe_id == recipe_id)
        .all()
    )

    lines: list[IngredientCostLine] = []
    total = Decimal("0")

    for ri in recipe_ingredients:
        unit_cost = get_latest_price(db, ri.ingredient_id)
        amount = Decimal(str(ri.amount))
        line_cost = (amount * unit_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total += line_cost

        ing_name = ri.ingredient.name if ri.ingredient else None

        lines.append(IngredientCostLine(
            ingredient_id=ri.ingredient_id,
            ingredient_name=ing_name,
            amount=amount,
            unit=ri.unit,
            unit_cost=unit_cost,
            line_cost=line_cost,
        ))

    base_yield = max(recipe.base_yield, 1)
    cost_per_portion = (total / Decimal(str(base_yield))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return CostBreakdown(
        recipe_id=recipe.id,
        recipe_name=recipe.name,
        base_yield=base_yield,
        total_cost=total,
        cost_per_portion=cost_per_portion,
        ingredients=lines,
    )


def cost_per_portion(db: Session, recipe_id: int) -> Decimal:
    """Quick cost-per-portion lookup."""
    breakdown = recipe_cost_breakdown(db, recipe_id)
    if breakdown:
        return breakdown.cost_per_portion
    return Decimal("0")
