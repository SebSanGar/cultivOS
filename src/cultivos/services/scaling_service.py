"""
Non-linear recipe scaling — the intelligence layer.

Pure functions: data in, results out. No DB, no HTTP.
"""

import math
from decimal import Decimal, ROUND_HALF_UP

from cultivos.models.recipe import ScaledIngredient


def scale_ingredient(
    base_amount: Decimal,
    scale_factor: Decimal,
    scaling_type: str = "linear",
    exponent: Decimal = Decimal("1.0"),
    step_size: Decimal | None = None,
) -> Decimal:
    """Scale a single ingredient amount using the appropriate curve.

    Scaling types:
      - linear:      amount * factor          (most ingredients)
      - sublinear:   amount * factor^exponent  (salt ~0.8, spices ~0.75)
      - logarithmic: amount * factor^exponent  (chili ~0.5)
      - fixed:       amount                    (vanilla extract, bay leaf)
      - stepped:     ceil(linear / step) * step (eggs, sheets of phyllo)
    """
    if scale_factor == Decimal("1"):
        return base_amount

    if scaling_type == "fixed":
        return base_amount

    if scaling_type == "stepped":
        linear = base_amount * scale_factor
        if step_size and step_size > 0:
            return (Decimal(math.ceil(linear / step_size)) * step_size).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
        return linear.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    # linear, sublinear, logarithmic — all use the exponent formula
    # scaled = base * factor^exponent
    factor_float = float(scale_factor)
    exponent_float = float(exponent)
    scaled = base_amount * Decimal(str(factor_float ** exponent_float))
    return scaled.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def scale_recipe(
    recipe_ingredients: list[dict],
    base_yield: int,
    target_yield: int,
    scaling_rules: dict[int, dict] | None = None,
) -> list[ScaledIngredient]:
    """Scale all ingredients in a recipe to a target yield.

    Args:
        recipe_ingredients: list of dicts with keys:
            ingredient_id, ingredient_name, amount (Decimal), unit, scaling_type
        base_yield: original recipe yield
        target_yield: desired yield
        scaling_rules: optional dict keyed by ingredient_id with keys:
            rule_type, exponent, step_size

    Returns:
        list of ScaledIngredient with base and scaled amounts.
    """
    if scaling_rules is None:
        scaling_rules = {}

    scale_factor = Decimal(str(target_yield)) / Decimal(str(base_yield))
    results = []

    for ri in recipe_ingredients:
        ing_id = ri["ingredient_id"]
        base_amount = Decimal(str(ri["amount"]))
        unit = ri["unit"]

        # Get scaling params: prefer explicit rule, fallback to ingredient's scaling_type
        rule = scaling_rules.get(ing_id, {})
        scaling_type = rule.get("rule_type", ri.get("scaling_type", "linear"))
        exponent = Decimal(str(rule.get("exponent", "1.0")))
        step_size = rule.get("step_size")
        if step_size is not None:
            step_size = Decimal(str(step_size))

        scaled = scale_ingredient(base_amount, scale_factor, scaling_type, exponent, step_size)

        results.append(ScaledIngredient(
            ingredient_id=ing_id,
            ingredient_name=ri.get("ingredient_name"),
            base_amount=base_amount,
            scaled_amount=scaled,
            unit=unit,
            scaling_type=scaling_type,
        ))

    return results


def scale_cooking_time(base_time_minutes: int, scale_factor: Decimal) -> int:
    """Estimate cooking time for larger batches.

    Cooking time scales roughly with the square root of the factor
    (larger batches need more time, but not linearly).
    """
    if base_time_minutes is None:
        return 0
    factor_float = float(scale_factor)
    return max(base_time_minutes, round(base_time_minutes * (factor_float ** 0.3)))
