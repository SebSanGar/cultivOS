"""Menu engineering — Star/Puzzle/Plowhorse/Dog classification.

Pure functions: data in, results out.
"""

from decimal import Decimal, ROUND_HALF_UP

from cultivos.models.financial import MenuEngineeringItem, MenuEngineeringMatrix


def classify_menu_item(
    margin: Decimal,
    popularity: int,
    avg_margin: Decimal,
    avg_popularity: Decimal,
) -> str:
    """Classify a menu item into the BCG-style matrix.

    | High margin + High popularity = Star    (promote)
    | High margin + Low popularity  = Puzzle  (reposition/reprice)
    | Low margin  + High popularity = Plowhorse (re-engineer cost)
    | Low margin  + Low popularity  = Dog     (remove/reinvent)
    """
    high_margin = margin >= avg_margin
    high_pop = Decimal(str(popularity)) >= avg_popularity

    if high_margin and high_pop:
        return "star"
    elif high_margin and not high_pop:
        return "puzzle"
    elif not high_margin and high_pop:
        return "plowhorse"
    else:
        return "dog"


def build_menu_matrix(
    items: list[dict],
) -> MenuEngineeringMatrix:
    """Build the full menu engineering matrix from recipe data.

    Each item dict should have:
        recipe_id, recipe_name, food_cost, menu_price (optional), popularity
    """
    if not items:
        return MenuEngineeringMatrix(
            location_id=0,
            items=[],
            avg_margin=Decimal("0"),
            avg_popularity=Decimal("0"),
            stars=0, puzzles=0, plowhorses=0, dogs=0,
        )

    # Calculate margins
    processed = []
    for item in items:
        food_cost = Decimal(str(item["food_cost"]))
        menu_price = Decimal(str(item.get("menu_price") or 0))
        margin = menu_price - food_cost if menu_price > 0 else Decimal("0")
        processed.append({
            **item,
            "food_cost": food_cost,
            "menu_price": menu_price,
            "margin": margin,
        })

    margins = [p["margin"] for p in processed]
    popularities = [p["popularity"] for p in processed]

    avg_margin = (sum(margins) / len(margins)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    avg_popularity = (Decimal(str(sum(popularities))) / Decimal(str(len(popularities)))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    classified = []
    counts = {"star": 0, "puzzle": 0, "plowhorse": 0, "dog": 0}

    for p in processed:
        cls = classify_menu_item(p["margin"], p["popularity"], avg_margin, avg_popularity)
        counts[cls] += 1
        classified.append(MenuEngineeringItem(
            recipe_id=p["recipe_id"],
            recipe_name=p["recipe_name"],
            food_cost=p["food_cost"],
            menu_price=p["menu_price"],
            margin=p["margin"],
            popularity=p["popularity"],
            classification=cls,
        ))

    location_id = items[0].get("location_id", 0) if items else 0

    return MenuEngineeringMatrix(
        location_id=location_id,
        items=classified,
        avg_margin=avg_margin,
        avg_popularity=avg_popularity,
        stars=counts["star"],
        puzzles=counts["puzzle"],
        plowhorses=counts["plowhorse"],
        dogs=counts["dog"],
    )


def food_cost_percentage(food_cost: Decimal, revenue: Decimal) -> Decimal:
    """Food cost % = food_cost / revenue * 100."""
    if revenue <= 0:
        return Decimal("0")
    return (food_cost / revenue * Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
