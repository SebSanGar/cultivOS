"""Integration tests for recipe API endpoints."""

from cultivos.db.models import Location


def _create_location(db):
    loc = Location(name="Test Kitchen", timezone="America/Toronto")
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


def test_create_recipe(client, db):
    loc = _create_location(db)
    res = client.post("/api/recipes", json={
        "name": "Chicken Salad",
        "category": "main",
        "location_id": loc.id,
        "base_yield": 10,
        "prep_time_minutes": 20,
        "allergens": ["nuts"],
        "tags": ["gluten-free"],
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Chicken Salad"
    assert data["base_yield"] == 10
    assert data["allergens"] == ["nuts"]


def test_list_recipes(client, db):
    loc = _create_location(db)
    client.post("/api/recipes", json={"name": "A", "location_id": loc.id, "base_yield": 1})
    client.post("/api/recipes", json={"name": "B", "location_id": loc.id, "base_yield": 1})
    res = client.get(f"/api/recipes?location_id={loc.id}")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_get_recipe_detail(client, db):
    loc = _create_location(db)
    r = client.post("/api/recipes", json={"name": "Soup", "location_id": loc.id, "base_yield": 4})
    recipe_id = r.json()["id"]

    # Add ingredient
    ing = client.post("/api/ingredients", json={"name": "Carrot", "location_id": loc.id})
    ing_id = ing.json()["id"]
    client.post(f"/api/recipes/{recipe_id}/ingredients", json={
        "ingredient_id": ing_id, "amount": "200", "unit": "g",
    })

    # Add step
    client.post(f"/api/recipes/{recipe_id}/steps", json={
        "step_order": 1, "instruction": "Dice carrots", "time_minutes": 5,
    })

    res = client.get(f"/api/recipes/{recipe_id}")
    assert res.status_code == 200
    data = res.json()
    assert len(data["ingredients"]) == 1
    assert len(data["steps"]) == 1
    assert data["ingredients"][0]["ingredient_name"] == "Carrot"


def test_scale_recipe_endpoint(client, db):
    loc = _create_location(db)
    r = client.post("/api/recipes", json={"name": "Bread", "location_id": loc.id, "base_yield": 10})
    recipe_id = r.json()["id"]

    # Flour (linear) and salt (sublinear)
    flour = client.post("/api/ingredients", json={"name": "Flour", "location_id": loc.id}).json()
    salt = client.post("/api/ingredients", json={"name": "Salt", "location_id": loc.id}).json()

    client.post(f"/api/recipes/{recipe_id}/ingredients", json={
        "ingredient_id": flour["id"], "amount": "500", "unit": "g",
    })
    client.post(f"/api/recipes/{recipe_id}/ingredients", json={
        "ingredient_id": salt["id"], "amount": "10", "unit": "g", "scaling_type": "sublinear",
    })
    client.post(f"/api/recipes/{recipe_id}/scaling-rules", json={
        "ingredient_id": salt["id"], "rule_type": "sublinear", "exponent": "0.8",
    })

    res = client.get(f"/api/recipes/{recipe_id}/scale?target_yield=100")
    assert res.status_code == 200
    data = res.json()
    assert data["target_yield"] == 100

    scaled_flour = next(i for i in data["ingredients"] if i["ingredient_id"] == flour["id"])
    scaled_salt = next(i for i in data["ingredients"] if i["ingredient_id"] == salt["id"])

    assert float(scaled_flour["scaled_amount"]) == 5000.0  # linear 10x
    assert float(scaled_salt["scaled_amount"]) < 100.0  # sublinear < linear


def test_delete_recipe_soft(client, db):
    loc = _create_location(db)
    r = client.post("/api/recipes", json={"name": "ToDelete", "location_id": loc.id, "base_yield": 1})
    recipe_id = r.json()["id"]

    res = client.delete(f"/api/recipes/{recipe_id}")
    assert res.status_code == 200

    # Should not appear in list
    res = client.get(f"/api/recipes?location_id={loc.id}")
    assert len(res.json()) == 0

    # But still in DB (soft delete)
    from cultivos.db.models import Recipe
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    assert recipe is not None
    assert recipe.deleted_at is not None


def test_recipe_not_found(client):
    res = client.get("/api/recipes/99999")
    assert res.status_code == 404
