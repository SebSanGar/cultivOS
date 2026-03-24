#!/usr/bin/env python3
"""
Seed script for Kitchen Intelligence MVP.

Creates demo data for a Toronto kitchen:
- 1 location
- 8 ingredients with prices from 2 suppliers
- 3 recipes with ingredients, steps, and scaling rules
- Par levels for each recipe
- Sample waste logs
- Shelf-life batches

Run: python -m scripts.seed
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cultivos.db.models import (
    Base,
    Ingredient,
    IngredientPrice,
    Location,
    ParLevel,
    Recipe,
    RecipeIngredient,
    RecipeStep,
    ScalingRule,
    ShelfLifeTracker,
    Supplier,
    WasteLog,
)

DB_URL = "sqlite:///cultivos.db"


def seed():
    engine = create_engine(DB_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    now = datetime.now(timezone.utc)

    # -----------------------------------------------------------------------
    # Location
    # -----------------------------------------------------------------------
    loc = Location(name="Demo Kitchen - Toronto", address="123 Queen St W, Toronto", timezone="America/Toronto", currency="CAD")
    db.add(loc)
    db.flush()
    print(f"  Location: {loc.name} (id={loc.id})")

    # -----------------------------------------------------------------------
    # Suppliers
    # -----------------------------------------------------------------------
    s1 = Supplier(name="Ontario Harvest Co.", contact_name="Maria", categories_json='["produce","dairy"]', payment_terms="net_30", location_id=loc.id)
    s2 = Supplier(name="GTA Protein Supply", contact_name="James", categories_json='["protein","seafood"]', payment_terms="net_15", location_id=loc.id)
    db.add_all([s1, s2])
    db.flush()
    print(f"  Suppliers: {s1.name}, {s2.name}")

    # -----------------------------------------------------------------------
    # Ingredients
    # -----------------------------------------------------------------------
    ingredients = {
        "chicken_breast": Ingredient(name="Chicken Breast", category="protein", default_unit="kg", location_id=loc.id),
        "salmon": Ingredient(name="Atlantic Salmon", category="protein", default_unit="kg", location_id=loc.id),
        "flour": Ingredient(name="All-Purpose Flour", category="grain", default_unit="kg", location_id=loc.id),
        "salt": Ingredient(name="Kosher Salt", category="spice", default_unit="g", location_id=loc.id),
        "olive_oil": Ingredient(name="Extra Virgin Olive Oil", category="other", default_unit="mL", location_id=loc.id),
        "lemon": Ingredient(name="Lemon", category="produce", default_unit="each", location_id=loc.id),
        "mixed_greens": Ingredient(name="Mixed Greens", category="produce", default_unit="kg", location_id=loc.id),
        "eggs": Ingredient(name="Large Eggs", category="dairy", default_unit="each", location_id=loc.id),
    }
    db.add_all(ingredients.values())
    db.flush()

    # Prices (CAD/unit)
    prices = [
        IngredientPrice(ingredient_id=ingredients["chicken_breast"].id, supplier_id=s2.id, price_per_unit=Decimal("14.50"), unit="kg"),
        IngredientPrice(ingredient_id=ingredients["salmon"].id, supplier_id=s2.id, price_per_unit=Decimal("28.00"), unit="kg"),
        IngredientPrice(ingredient_id=ingredients["flour"].id, supplier_id=s1.id, price_per_unit=Decimal("1.80"), unit="kg"),
        IngredientPrice(ingredient_id=ingredients["salt"].id, supplier_id=s1.id, price_per_unit=Decimal("0.005"), unit="g"),
        IngredientPrice(ingredient_id=ingredients["olive_oil"].id, supplier_id=s1.id, price_per_unit=Decimal("0.02"), unit="mL"),
        IngredientPrice(ingredient_id=ingredients["lemon"].id, supplier_id=s1.id, price_per_unit=Decimal("0.75"), unit="each"),
        IngredientPrice(ingredient_id=ingredients["mixed_greens"].id, supplier_id=s1.id, price_per_unit=Decimal("12.00"), unit="kg"),
        IngredientPrice(ingredient_id=ingredients["eggs"].id, supplier_id=s1.id, price_per_unit=Decimal("0.45"), unit="each"),
    ]
    db.add_all(prices)
    db.flush()
    print(f"  Ingredients: {len(ingredients)} with prices")

    # -----------------------------------------------------------------------
    # Recipe 1: Grilled Chicken Salad (10 portions)
    # -----------------------------------------------------------------------
    r1 = Recipe(
        name="Grilled Chicken Salad", category="main", location_id=loc.id,
        base_yield=10, prep_time_minutes=15, cook_time_minutes=12,
        total_time_minutes=27, shelf_life_hours=4,
        allergens_json='["eggs"]', tags_json='["gluten-free","high-protein"]',
    )
    db.add(r1)
    db.flush()

    r1_ingredients = [
        RecipeIngredient(recipe_id=r1.id, ingredient_id=ingredients["chicken_breast"].id, amount=Decimal("2.0"), unit="kg", scaling_type="linear"),
        RecipeIngredient(recipe_id=r1.id, ingredient_id=ingredients["mixed_greens"].id, amount=Decimal("0.5"), unit="kg", scaling_type="linear"),
        RecipeIngredient(recipe_id=r1.id, ingredient_id=ingredients["olive_oil"].id, amount=Decimal("60"), unit="mL", scaling_type="sublinear"),
        RecipeIngredient(recipe_id=r1.id, ingredient_id=ingredients["lemon"].id, amount=Decimal("2"), unit="each", scaling_type="stepped"),
        RecipeIngredient(recipe_id=r1.id, ingredient_id=ingredients["salt"].id, amount=Decimal("15"), unit="g", scaling_type="sublinear"),
    ]
    db.add_all(r1_ingredients)

    r1_steps = [
        RecipeStep(recipe_id=r1.id, step_order=1, instruction="Season chicken breasts with salt, pepper, and olive oil", time_minutes=3),
        RecipeStep(recipe_id=r1.id, step_order=2, instruction="Grill chicken at 200C until internal temp reaches 74C", time_minutes=12, temperature_c=200),
        RecipeStep(recipe_id=r1.id, step_order=3, instruction="Rest chicken 5 min, slice into strips", time_minutes=5),
        RecipeStep(recipe_id=r1.id, step_order=4, instruction="Toss mixed greens with lemon-olive oil dressing, top with chicken", time_minutes=2),
    ]
    db.add_all(r1_steps)

    r1_rules = [
        ScalingRule(recipe_id=r1.id, ingredient_id=ingredients["olive_oil"].id, rule_type="sublinear", exponent=Decimal("0.85")),
        ScalingRule(recipe_id=r1.id, ingredient_id=ingredients["lemon"].id, rule_type="stepped", exponent=Decimal("1.0"), step_size=Decimal("1")),
        ScalingRule(recipe_id=r1.id, ingredient_id=ingredients["salt"].id, rule_type="sublinear", exponent=Decimal("0.8")),
    ]
    db.add_all(r1_rules)
    db.flush()

    # -----------------------------------------------------------------------
    # Recipe 2: Pan-Seared Salmon (8 portions)
    # -----------------------------------------------------------------------
    r2 = Recipe(
        name="Pan-Seared Salmon", category="main", location_id=loc.id,
        base_yield=8, prep_time_minutes=10, cook_time_minutes=8,
        total_time_minutes=18, shelf_life_hours=2,
        allergens_json='["fish"]', tags_json='["gluten-free","omega-3"]',
    )
    db.add(r2)
    db.flush()

    r2_ingredients = [
        RecipeIngredient(recipe_id=r2.id, ingredient_id=ingredients["salmon"].id, amount=Decimal("1.6"), unit="kg", scaling_type="linear"),
        RecipeIngredient(recipe_id=r2.id, ingredient_id=ingredients["olive_oil"].id, amount=Decimal("40"), unit="mL", scaling_type="sublinear"),
        RecipeIngredient(recipe_id=r2.id, ingredient_id=ingredients["lemon"].id, amount=Decimal("2"), unit="each", scaling_type="stepped"),
        RecipeIngredient(recipe_id=r2.id, ingredient_id=ingredients["salt"].id, amount=Decimal("10"), unit="g", scaling_type="sublinear"),
    ]
    db.add_all(r2_ingredients)

    r2_rules = [
        ScalingRule(recipe_id=r2.id, ingredient_id=ingredients["olive_oil"].id, rule_type="sublinear", exponent=Decimal("0.85")),
        ScalingRule(recipe_id=r2.id, ingredient_id=ingredients["lemon"].id, rule_type="stepped", exponent=Decimal("1.0"), step_size=Decimal("1")),
        ScalingRule(recipe_id=r2.id, ingredient_id=ingredients["salt"].id, rule_type="sublinear", exponent=Decimal("0.8")),
    ]
    db.add_all(r2_rules)
    db.flush()

    # -----------------------------------------------------------------------
    # Recipe 3: House Focaccia (20 portions)
    # -----------------------------------------------------------------------
    r3 = Recipe(
        name="House Focaccia", category="base", location_id=loc.id,
        base_yield=20, prep_time_minutes=20, cook_time_minutes=25,
        total_time_minutes=45, shelf_life_hours=24,
        allergens_json='["gluten","eggs"]', tags_json='["vegetarian","house-bread"]',
    )
    db.add(r3)
    db.flush()

    r3_ingredients = [
        RecipeIngredient(recipe_id=r3.id, ingredient_id=ingredients["flour"].id, amount=Decimal("1.0"), unit="kg", scaling_type="linear"),
        RecipeIngredient(recipe_id=r3.id, ingredient_id=ingredients["olive_oil"].id, amount=Decimal("100"), unit="mL", scaling_type="sublinear"),
        RecipeIngredient(recipe_id=r3.id, ingredient_id=ingredients["salt"].id, amount=Decimal("20"), unit="g", scaling_type="sublinear"),
        RecipeIngredient(recipe_id=r3.id, ingredient_id=ingredients["eggs"].id, amount=Decimal("3"), unit="each", scaling_type="stepped"),
    ]
    db.add_all(r3_ingredients)

    r3_rules = [
        ScalingRule(recipe_id=r3.id, ingredient_id=ingredients["olive_oil"].id, rule_type="sublinear", exponent=Decimal("0.85")),
        ScalingRule(recipe_id=r3.id, ingredient_id=ingredients["salt"].id, rule_type="sublinear", exponent=Decimal("0.8")),
        ScalingRule(recipe_id=r3.id, ingredient_id=ingredients["eggs"].id, rule_type="stepped", exponent=Decimal("1.0"), step_size=Decimal("1")),
    ]
    db.add_all(r3_rules)
    db.flush()

    print(f"  Recipes: {r1.name}, {r2.name}, {r3.name}")

    # -----------------------------------------------------------------------
    # Par levels
    # -----------------------------------------------------------------------
    pars = [
        ParLevel(recipe_id=r1.id, location_id=loc.id, base_par=40, safety_buffer=12, effective_par=52),
        ParLevel(recipe_id=r2.id, location_id=loc.id, base_par=25, safety_buffer=8, effective_par=33),
        ParLevel(recipe_id=r3.id, location_id=loc.id, base_par=60, safety_buffer=15, effective_par=75),
    ]
    db.add_all(pars)
    db.flush()
    print(f"  Par levels set for all 3 recipes")

    # -----------------------------------------------------------------------
    # Shelf-life batches (today's production)
    # -----------------------------------------------------------------------
    batches = [
        ShelfLifeTracker(recipe_id=r1.id, location_id=loc.id, produced_at=now - timedelta(hours=2), expires_at=now + timedelta(hours=2), quantity_produced=30, quantity_remaining=22),
        ShelfLifeTracker(recipe_id=r2.id, location_id=loc.id, produced_at=now - timedelta(hours=1), expires_at=now + timedelta(hours=1), quantity_produced=15, quantity_remaining=15, status="use_soon"),
        ShelfLifeTracker(recipe_id=r3.id, location_id=loc.id, produced_at=now - timedelta(hours=6), expires_at=now + timedelta(hours=18), quantity_produced=40, quantity_remaining=28),
    ]
    db.add_all(batches)
    db.flush()
    print(f"  Shelf-life batches: 3 active")

    # -----------------------------------------------------------------------
    # Waste logs (last 3 days)
    # -----------------------------------------------------------------------
    waste = [
        WasteLog(location_id=loc.id, logged_at=now - timedelta(days=2), recipe_id=r1.id, category="overproduction", quantity=Decimal("3"), unit="portions", cost_estimate=Decimal("12.60")),
        WasteLog(location_id=loc.id, logged_at=now - timedelta(days=1), ingredient_id=ingredients["mixed_greens"].id, category="spoilage", quantity=Decimal("0.8"), unit="kg", cost_estimate=Decimal("9.60"), reason="Missed rotation"),
        WasteLog(location_id=loc.id, logged_at=now - timedelta(hours=4), recipe_id=r2.id, category="plate", quantity=Decimal("2"), unit="portions", cost_estimate=Decimal("14.00")),
        WasteLog(location_id=loc.id, logged_at=now - timedelta(hours=1), ingredient_id=ingredients["lemon"].id, category="trim", quantity=Decimal("0.3"), unit="kg", cost_estimate=Decimal("2.25")),
    ]
    db.add_all(waste)

    db.commit()
    print("\nSeed complete. Explore at http://localhost:8000/docs")
    print(f"\nKey IDs:")
    print(f"  location_id = {loc.id}")
    print(f"  recipe_ids  = {r1.id} (Chicken Salad), {r2.id} (Salmon), {r3.id} (Focaccia)")
    print(f"\nTry:")
    print(f"  GET /api/recipes/{r1.id}/scale?target_yield=100")
    print(f"  GET /api/recipes/{r1.id}/cost")
    print(f"  GET /api/production/needs?location_id={loc.id}")
    print(f"  GET /api/menu-engineering?location_id={loc.id}")
    db.close()


if __name__ == "__main__":
    print("Seeding Kitchen Intelligence MVP...\n")
    seed()
