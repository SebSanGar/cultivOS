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
    DishDNA,
    DishEvolution,
    Ingredient,
    IngredientAffinity,
    IngredientPrice,
    IngredientSeason,
    Location,
    ParLevel,
    Recipe,
    RecipeIngredient,
    RecipeStep,
    RecipeTechnique,
    ScalingRule,
    ShelfLifeTracker,
    Supplier,
    Technique,
    User,
    WasteLog,
)
from cultivos.services.auth_service import hash_pin

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
    # Users (demo PINs — change in production!)
    # -----------------------------------------------------------------------
    users = {
        "admin": User(name="Admin Seb", email="seb@hungry-cooks.com", role="admin", pin_hash=hash_pin("0000"), location_id=loc.id),
        "manager": User(name="Manager Maria", email="maria@hungry-cooks.com", role="manager", pin_hash=hash_pin("1111"), location_id=loc.id),
        "lead": User(name="Lead Chef Carlos", role="lead", pin_hash=hash_pin("2222"), location_id=loc.id),
        "staff": User(name="Cook Ana", role="staff", pin_hash=hash_pin("3333"), location_id=loc.id),
    }
    db.add_all(users.values())
    db.flush()
    print(f"  Users: {len(users)} (admin=0000, manager=1111, lead=2222, staff=3333)")

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
    db.flush()

    # -----------------------------------------------------------------------
    # Culinary Intelligence: Techniques (18 across 7 categories)
    # -----------------------------------------------------------------------
    techniques = {
        # Heat (6)
        "grill": Technique(name="Grill", category="Heat", subcategory="Direct heat", description="Cook over direct flame or heat source", difficulty_level=2, equipment_required_json='["grill"]', time_profile="medium", best_for_json='["proteins","vegetables"]', season_affinity_json='["summer","year-round"]', flavor_impact="Smoky char, Maillard reaction", texture_impact="Crispy exterior, tender interior", location_id=loc.id),
        "sear": Technique(name="Sear", category="Heat", subcategory="Pan heat", description="High-heat browning in a pan", difficulty_level=2, equipment_required_json='["saute pan"]', time_profile="quick", best_for_json='["proteins","seafood"]', season_affinity_json='["year-round"]', flavor_impact="Deep Maillard crust, caramelized", texture_impact="Crispy crust, juicy interior", location_id=loc.id),
        "roast": Technique(name="Roast", category="Heat", subcategory="Oven heat", description="Dry heat cooking in oven", difficulty_level=1, equipment_required_json='["oven"]', time_profile="long", best_for_json='["proteins","vegetables","grains"]', season_affinity_json='["fall","winter"]', flavor_impact="Deep caramelization, concentrated flavors", texture_impact="Crispy exterior, tender throughout", location_id=loc.id),
        "saute": Technique(name="Saute", category="Heat", subcategory="Pan heat", description="Quick cooking in small amount of fat", difficulty_level=1, equipment_required_json='["saute pan"]', time_profile="quick", best_for_json='["vegetables","proteins"]', season_affinity_json='["year-round"]', flavor_impact="Light browning, fresh flavor retained", texture_impact="Tender-crisp", location_id=loc.id),
        "braise": Technique(name="Braise", category="Heat", subcategory="Wet-dry heat", description="Sear then slow cook in liquid", difficulty_level=3, equipment_required_json='["dutch oven"]', time_profile="long", best_for_json='["proteins","vegetables"]', season_affinity_json='["fall","winter"]', flavor_impact="Deep, complex, concentrated", texture_impact="Fork-tender, falling apart", location_id=loc.id),
        "sous_vide": Technique(name="Sous Vide", category="Heat", subcategory="Precision heat", description="Vacuum-sealed precision cooking in water bath", difficulty_level=3, equipment_required_json='["immersion circulator","vacuum sealer"]', time_profile="long", best_for_json='["proteins","eggs"]', season_affinity_json='["year-round"]', flavor_impact="Pure, concentrated ingredient flavor", texture_impact="Perfectly uniform doneness", location_id=loc.id),
        # Cold (3)
        "ceviche": Technique(name="Ceviche Cure", category="Cold", subcategory="Acid cure", description="Denature proteins with citrus acid", difficulty_level=2, equipment_required_json='[]', time_profile="medium", best_for_json='["seafood"]', season_affinity_json='["summer"]', flavor_impact="Bright, acidic, fresh", texture_impact="Firm exterior, silky interior", location_id=loc.id),
        "cold_smoke": Technique(name="Cold Smoke", category="Cold", subcategory="Smoke", description="Smoke without cooking", difficulty_level=4, equipment_required_json='["cold smoker"]', time_profile="long", best_for_json='["proteins","seafood","dairy"]', season_affinity_json='["fall","winter"]', flavor_impact="Delicate smoke, complex", texture_impact="Unchanged original texture", location_id=loc.id),
        "crudo": Technique(name="Crudo", category="Cold", subcategory="Raw preparation", description="Serve raw with minimal dressing", difficulty_level=2, equipment_required_json='[]', time_profile="quick", best_for_json='["seafood"]', season_affinity_json='["summer"]', flavor_impact="Pure, clean, bright", texture_impact="Buttery, silky", location_id=loc.id),
        # Texture (3)
        "emulsify": Technique(name="Emulsify", category="Texture", subcategory="Binding", description="Combine immiscible liquids into stable mixture", difficulty_level=3, equipment_required_json='["whisk","blender"]', time_profile="quick", best_for_json='["sauces","dressings"]', season_affinity_json='["year-round"]', flavor_impact="Rounded, balanced mouthfeel", texture_impact="Creamy, smooth, cohesive", location_id=loc.id),
        "crisp": Technique(name="Crisp", category="Texture", subcategory="Dehydration", description="Remove moisture for crunch", difficulty_level=2, equipment_required_json='["oven","fryer"]', time_profile="medium", best_for_json='["vegetables","grains","proteins"]', season_affinity_json='["year-round"]', flavor_impact="Concentrated, toasted", texture_impact="Crunchy, shattering", location_id=loc.id),
        "puree": Technique(name="Puree", category="Texture", subcategory="Blending", description="Blend to smooth consistency", difficulty_level=1, equipment_required_json='["blender"]', time_profile="quick", best_for_json='["vegetables","fruits"]', season_affinity_json='["year-round"]', flavor_impact="Concentrated, smooth", texture_impact="Velvety, smooth", location_id=loc.id),
        # Flavor (3)
        "marinate": Technique(name="Marinate", category="Flavor", subcategory="Infusion", description="Soak in seasoned liquid to infuse flavor", difficulty_level=1, equipment_required_json='[]', time_profile="long", best_for_json='["proteins","vegetables"]', season_affinity_json='["year-round"]', flavor_impact="Layered, penetrating seasoning", texture_impact="Tenderized surface", location_id=loc.id),
        "deglaze": Technique(name="Deglaze", category="Flavor", subcategory="Extraction", description="Dissolve caramelized fond with liquid", difficulty_level=2, equipment_required_json='["saute pan"]', time_profile="quick", best_for_json='["sauces"]', season_affinity_json='["year-round"]', flavor_impact="Rich, concentrated pan sauce", texture_impact="Liquid, silky", location_id=loc.id),
        "caramelize": Technique(name="Caramelize", category="Flavor", subcategory="Sugar browning", description="Brown sugars through controlled heat", difficulty_level=2, equipment_required_json='["saute pan"]', time_profile="medium", best_for_json='["vegetables","fruits"]', season_affinity_json='["fall","winter"]', flavor_impact="Sweet, nutty, complex", texture_impact="Soft, jammy", location_id=loc.id),
        # Preservation (2)
        "pickle": Technique(name="Pickle", category="Preservation", subcategory="Acid preservation", description="Preserve in vinegar brine", difficulty_level=1, equipment_required_json='["jars"]', time_profile="long", best_for_json='["vegetables"]', season_affinity_json='["summer","fall"]', flavor_impact="Sharp acid, tangy, bright", texture_impact="Firm, crisp-tender", location_id=loc.id),
        "confit": Technique(name="Confit", category="Preservation", subcategory="Fat preservation", description="Slow cook submerged in fat", difficulty_level=3, equipment_required_json='["dutch oven"]', time_profile="long", best_for_json='["proteins","vegetables"]', season_affinity_json='["fall","winter"]', flavor_impact="Rich, luscious, deep", texture_impact="Silky, melt-in-mouth, tender", location_id=loc.id),
        # Assembly (1)
        "compose": Technique(name="Compose/Plate", category="Assembly", subcategory="Plating", description="Arrange components for visual and textural balance", difficulty_level=2, equipment_required_json='[]', time_profile="quick", best_for_json='["all"]', season_affinity_json='["year-round"]', flavor_impact="Balanced bite combinations", texture_impact="Varied textures per bite", location_id=loc.id),
    }
    db.add_all(techniques.values())
    db.flush()
    print(f"  Techniques: {len(techniques)} across 7 categories")

    # -----------------------------------------------------------------------
    # Recipe-Technique links
    # -----------------------------------------------------------------------
    recipe_techniques = [
        # Grilled Chicken Salad: grill, compose
        RecipeTechnique(recipe_id=r1.id, technique_id=techniques["grill"].id, step_order=1),
        RecipeTechnique(recipe_id=r1.id, technique_id=techniques["compose"].id, step_order=2),
        # Pan-Seared Salmon: sear, deglaze, compose
        RecipeTechnique(recipe_id=r2.id, technique_id=techniques["sear"].id, step_order=1),
        RecipeTechnique(recipe_id=r2.id, technique_id=techniques["deglaze"].id, step_order=2),
        RecipeTechnique(recipe_id=r2.id, technique_id=techniques["compose"].id, step_order=3),
        # House Focaccia: emulsify, roast
        RecipeTechnique(recipe_id=r3.id, technique_id=techniques["emulsify"].id, step_order=1),
        RecipeTechnique(recipe_id=r3.id, technique_id=techniques["roast"].id, step_order=2),
    ]
    db.add_all(recipe_techniques)
    db.flush()
    print(f"  Recipe-technique links: {len(recipe_techniques)}")

    # -----------------------------------------------------------------------
    # DishDNA for each recipe
    # -----------------------------------------------------------------------
    dna_entries = [
        DishDNA(
            recipe_id=r1.id,
            technique_fingerprint_json=json.dumps([techniques["grill"].id, techniques["compose"].id]),
            flavor_profile_json=json.dumps({"savory": 6, "sweet": 0, "acid": 3, "bitter": 3, "umami": 3}),
            texture_profile_json=json.dumps({"crispy": 6, "creamy": 0, "chewy": 0, "tender": 3}),
            cuisine_influences_json=json.dumps(["Mediterranean", "North American"]),
            seasonal_peak="summer",
            complexity_score=6,
        ),
        DishDNA(
            recipe_id=r2.id,
            technique_fingerprint_json=json.dumps([techniques["sear"].id, techniques["deglaze"].id, techniques["compose"].id]),
            flavor_profile_json=json.dumps({"savory": 8, "sweet": 0, "acid": 3, "bitter": 0, "umami": 6}),
            texture_profile_json=json.dumps({"crispy": 6, "creamy": 3, "chewy": 0, "tender": 3}),
            cuisine_influences_json=json.dumps(["French", "North American"]),
            seasonal_peak="fall",
            complexity_score=7,
        ),
        DishDNA(
            recipe_id=r3.id,
            technique_fingerprint_json=json.dumps([techniques["emulsify"].id, techniques["roast"].id]),
            flavor_profile_json=json.dumps({"savory": 3, "sweet": 3, "acid": 0, "bitter": 0, "umami": 3}),
            texture_profile_json=json.dumps({"crispy": 6, "creamy": 3, "chewy": 3, "tender": 0}),
            cuisine_influences_json=json.dumps(["Italian"]),
            seasonal_peak="year-round",
            complexity_score=5,
        ),
    ]
    db.add_all(dna_entries)
    db.flush()
    print(f"  DishDNA: generated for all 3 recipes")

    # -----------------------------------------------------------------------
    # Dish Evolution: Chicken Salad evolved from Basic Chicken Plate
    # -----------------------------------------------------------------------
    evo = DishEvolution(
        recipe_id=r1.id,
        parent_recipe_id=None,
        generation=2,
        evolution_type="seasonal_swap",
        changelog_json=json.dumps([
            "Swapped iceberg lettuce for seasonal mixed greens",
            "Added grilled lemon half as garnish",
            "Upgraded to herb-marinated chicken breast",
        ]),
        techniques_added_json=json.dumps([techniques["grill"].id]),
        techniques_removed_json=json.dumps([]),
        ingredients_swapped_json=json.dumps([
            {"old": "Iceberg lettuce", "new": "Mixed greens", "reason": "Seasonal availability, better nutrition"},
        ]),
        performance_delta_json=json.dumps({"margin_change": 1.20, "popularity_change": 15, "waste_change": -8}),
        evolved_by="Chef Maria",
    )
    db.add(evo)
    db.flush()
    print(f"  Evolution: Chicken Salad lineage (gen 2)")

    # -----------------------------------------------------------------------
    # Ingredient Affinities (pairings)
    # -----------------------------------------------------------------------
    affinities = [
        IngredientAffinity(ingredient_a_id=ingredients["chicken_breast"].id, ingredient_b_id=ingredients["lemon"].id, strength_score=Decimal("9.0"), notes="Classic Mediterranean pairing"),
        IngredientAffinity(ingredient_a_id=ingredients["chicken_breast"].id, ingredient_b_id=ingredients["olive_oil"].id, strength_score=Decimal("8.0")),
        IngredientAffinity(ingredient_a_id=ingredients["chicken_breast"].id, ingredient_b_id=ingredients["mixed_greens"].id, strength_score=Decimal("7.0")),
        IngredientAffinity(ingredient_a_id=ingredients["salmon"].id, ingredient_b_id=ingredients["lemon"].id, strength_score=Decimal("9.0"), notes="Essential fish pairing"),
        IngredientAffinity(ingredient_a_id=ingredients["salmon"].id, ingredient_b_id=ingredients["olive_oil"].id, strength_score=Decimal("8.0")),
        IngredientAffinity(ingredient_a_id=ingredients["flour"].id, ingredient_b_id=ingredients["eggs"].id, strength_score=Decimal("9.0"), notes="Foundational baking bond"),
        IngredientAffinity(ingredient_a_id=ingredients["flour"].id, ingredient_b_id=ingredients["olive_oil"].id, strength_score=Decimal("7.0")),
        IngredientAffinity(ingredient_a_id=ingredients["lemon"].id, ingredient_b_id=ingredients["olive_oil"].id, strength_score=Decimal("8.5"), notes="Classic vinaigrette base"),
    ]
    db.add_all(affinities)
    db.flush()
    print(f"  Affinities: {len(affinities)} ingredient pairings")

    # -----------------------------------------------------------------------
    # Seasonal availability (Ontario calendar)
    # -----------------------------------------------------------------------
    seasons = [
        IngredientSeason(ingredient_id=ingredients["chicken_breast"].id, season="year-round", is_peak=False, months_json=json.dumps([1,2,3,4,5,6,7,8,9,10,11,12])),
        IngredientSeason(ingredient_id=ingredients["salmon"].id, season="summer", is_peak=True, months_json=json.dumps([6,7,8,9])),
        IngredientSeason(ingredient_id=ingredients["salmon"].id, season="fall", is_peak=False, months_json=json.dumps([10,11])),
        IngredientSeason(ingredient_id=ingredients["mixed_greens"].id, season="spring", is_peak=True, months_json=json.dumps([4,5,6])),
        IngredientSeason(ingredient_id=ingredients["mixed_greens"].id, season="summer", is_peak=True, months_json=json.dumps([7,8,9])),
        IngredientSeason(ingredient_id=ingredients["mixed_greens"].id, season="fall", is_peak=False, months_json=json.dumps([10])),
        IngredientSeason(ingredient_id=ingredients["lemon"].id, season="winter", is_peak=True, months_json=json.dumps([12,1,2,3])),
        IngredientSeason(ingredient_id=ingredients["eggs"].id, season="spring", is_peak=True, months_json=json.dumps([3,4,5])),
        IngredientSeason(ingredient_id=ingredients["eggs"].id, season="year-round", is_peak=False, months_json=json.dumps([1,2,3,4,5,6,7,8,9,10,11,12])),
    ]
    db.add_all(seasons)
    db.flush()
    print(f"  Seasonal data: {len(seasons)} entries (Ontario calendar)")

    db.commit()
    print("\nSeed complete. Explore at http://localhost:8000/docs")
    print(f"\nKey IDs:")
    print(f"  location_id = {loc.id}")
    print(f"  recipe_ids  = {r1.id} (Chicken Salad), {r2.id} (Salmon), {r3.id} (Focaccia)")
    print(f"  user_ids    = {users['admin'].id} (Admin/0000), {users['manager'].id} (Manager/1111), {users['lead'].id} (Lead/2222), {users['staff'].id} (Staff/3333)")
    print(f"\nTry:")
    print(f"  POST /api/auth/login  {{\"user_id\": {users['admin'].id}, \"pin\": \"0000\"}}")
    print(f"  GET /api/recipes/{r1.id}/scale?target_yield=100")
    print(f"  GET /api/recipes/{r1.id}/cost")
    print(f"  GET /api/recipes/{r1.id}/dna")
    print(f"  GET /api/recipes/{r1.id}/lineage")
    print(f"  GET /api/techniques/audit?location_id={loc.id}")
    print(f"  GET /api/menu/dna-comparison?location_id={loc.id}")
    print(f"  GET /api/ingredients/{ingredients['chicken_breast'].id}/affinities")
    print(f"  GET /api/production/needs?location_id={loc.id}")
    print(f"  GET /api/menu-engineering?location_id={loc.id}")
    db.close()


if __name__ == "__main__":
    print("Seeding Kitchen Intelligence MVP...\n")
    seed()
