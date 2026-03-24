"""Integration tests for culinary intelligence API."""

from cultivos.db.models import Location


def _setup(client, db):
    loc = Location(name="Test Kitchen", timezone="America/Toronto")
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


def test_create_technique(client, db):
    loc = _setup(client, db)
    res = client.post("/api/techniques", json={
        "name": "Grill",
        "category": "Heat",
        "description": "Cook over direct heat",
        "difficulty_level": 2,
        "equipment_required": ["grill"],
        "time_profile": "medium",
        "best_for": ["proteins", "vegetables"],
        "flavor_impact": "Smoky char, Maillard reaction",
        "texture_impact": "Crispy exterior, tender interior",
        "location_id": loc.id,
    })
    assert res.status_code == 201
    assert res.json()["name"] == "Grill"
    assert res.json()["category"] == "Heat"


def test_list_techniques_by_category(client, db):
    loc = _setup(client, db)
    client.post("/api/techniques", json={"name": "Grill", "category": "Heat", "location_id": loc.id})
    client.post("/api/techniques", json={"name": "Sear", "category": "Heat", "location_id": loc.id})
    client.post("/api/techniques", json={"name": "Pickle", "category": "Preservation", "location_id": loc.id})

    res = client.get(f"/api/techniques?location_id={loc.id}&category=Heat")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_link_technique_to_recipe(client, db):
    loc = _setup(client, db)
    tech = client.post("/api/techniques", json={"name": "Grill", "category": "Heat", "location_id": loc.id}).json()
    recipe = client.post("/api/recipes", json={"name": "Grilled Chicken", "location_id": loc.id, "base_yield": 4}).json()

    res = client.post(f"/api/recipes/{recipe['id']}/techniques", json={
        "technique_id": tech["id"], "step_order": 1,
    })
    assert res.status_code == 201
    assert res.json()["technique_name"] == "Grill"

    # Verify retrieval
    res = client.get(f"/api/recipes/{recipe['id']}/techniques")
    assert len(res.json()) == 1


def test_generate_and_get_dna(client, db):
    loc = _setup(client, db)
    recipe = client.post("/api/recipes", json={"name": "Soup", "location_id": loc.id, "base_yield": 10}).json()
    ing = client.post("/api/ingredients", json={"name": "Carrot", "location_id": loc.id}).json()
    client.post(f"/api/recipes/{recipe['id']}/ingredients", json={"ingredient_id": ing["id"], "amount": "200", "unit": "g"})
    client.post(f"/api/recipes/{recipe['id']}/steps", json={"step_order": 1, "instruction": "Boil"})

    tech = client.post("/api/techniques", json={
        "name": "Braise", "category": "Heat", "location_id": loc.id,
        "flavor_impact": "Deep savory", "texture_impact": "Tender",
    }).json()
    client.post(f"/api/recipes/{recipe['id']}/techniques", json={"technique_id": tech["id"], "step_order": 1})

    # Generate DNA
    res = client.post(f"/api/recipes/{recipe['id']}/dna/generate")
    assert res.status_code == 200
    dna = res.json()
    assert dna["recipe_id"] == recipe["id"]
    assert dna["complexity_score"] >= 1
    assert tech["id"] in dna["technique_fingerprint"]

    # Retrieve stored DNA
    res = client.get(f"/api/recipes/{recipe['id']}/dna")
    assert res.status_code == 200
    assert res.json()["complexity_score"] == dna["complexity_score"]


def test_log_evolution_and_lineage(client, db):
    loc = _setup(client, db)
    recipe = client.post("/api/recipes", json={"name": "Chicken v2", "location_id": loc.id, "base_yield": 10}).json()

    res = client.post(f"/api/recipes/{recipe['id']}/evolve", json={
        "recipe_id": recipe["id"],
        "generation": 2,
        "evolution_type": "seasonal_swap",
        "changelog": ["Swapped summer greens for roasted root vegetables"],
        "evolved_by": "Chef Maria",
    })
    assert res.status_code == 201
    assert res.json()["evolution_type"] == "seasonal_swap"

    res = client.get(f"/api/recipes/{recipe['id']}/lineage")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["evolved_by"] == "Chef Maria"


def test_technique_audit_endpoint(client, db):
    loc = _setup(client, db)
    t1 = client.post("/api/techniques", json={"name": "Grill", "category": "Heat", "location_id": loc.id}).json()
    client.post("/api/techniques", json={"name": "Sear", "category": "Heat", "location_id": loc.id})
    client.post("/api/techniques", json={"name": "Pickle", "category": "Preservation", "location_id": loc.id})

    # Link only Grill to a recipe
    recipe = client.post("/api/recipes", json={"name": "Test", "location_id": loc.id, "base_yield": 1}).json()
    client.post(f"/api/recipes/{recipe['id']}/techniques", json={"technique_id": t1["id"]})

    res = client.get(f"/api/techniques/audit?location_id={loc.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["total_techniques"] == 3
    assert data["in_use_count"] == 1
    assert data["overall_score"] < 10


def test_dna_comparison_endpoint(client, db):
    loc = _setup(client, db)
    # Create 2 recipes with different techniques
    t1 = client.post("/api/techniques", json={"name": "Grill", "category": "Heat", "location_id": loc.id, "flavor_impact": "Char", "texture_impact": "Crispy"}).json()
    t2 = client.post("/api/techniques", json={"name": "Braise", "category": "Heat", "location_id": loc.id, "flavor_impact": "Deep", "texture_impact": "Tender"}).json()

    r1 = client.post("/api/recipes", json={"name": "A", "location_id": loc.id, "base_yield": 1}).json()
    r2 = client.post("/api/recipes", json={"name": "B", "location_id": loc.id, "base_yield": 1}).json()

    client.post(f"/api/recipes/{r1['id']}/techniques", json={"technique_id": t1["id"]})
    client.post(f"/api/recipes/{r2['id']}/techniques", json={"technique_id": t2["id"]})

    # Generate DNA for both
    client.post(f"/api/recipes/{r1['id']}/dna/generate")
    client.post(f"/api/recipes/{r2['id']}/dna/generate")

    res = client.get(f"/api/menu/dna-comparison?location_id={loc.id}")
    assert res.status_code == 200
    data = res.json()
    assert len(data["pairs"]) == 1


def test_add_and_get_affinities(client, db):
    loc = _setup(client, db)
    chicken = client.post("/api/ingredients", json={"name": "Chicken", "location_id": loc.id}).json()
    lemon = client.post("/api/ingredients", json={"name": "Lemon", "location_id": loc.id}).json()

    res = client.post("/api/ingredient-affinities", json={
        "ingredient_a_id": chicken["id"],
        "ingredient_b_id": lemon["id"],
        "strength_score": "9.0",
        "notes": "Classic pairing",
    })
    assert res.status_code == 201
    assert res.json()["ingredient_a_name"] == "Chicken"
    assert res.json()["ingredient_b_name"] == "Lemon"

    # Retrieve from either side
    res = client.get(f"/api/ingredients/{chicken['id']}/affinities")
    assert len(res.json()) == 1
    res = client.get(f"/api/ingredients/{lemon['id']}/affinities")
    assert len(res.json()) == 1
