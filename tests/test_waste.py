"""Tests for waste tracking."""

from datetime import datetime, timedelta, timezone

from cultivos.db.models import Location


def _setup(client, db):
    loc = Location(name="Test Kitchen", timezone="America/Toronto")
    db.add(loc)
    db.commit()
    db.refresh(loc)
    ing = client.post("/api/ingredients", json={"name": "Lettuce", "location_id": loc.id}).json()
    return loc, ing


def test_log_waste(client, db):
    loc, ing = _setup(client, db)
    res = client.post("/api/waste", json={
        "location_id": loc.id,
        "ingredient_id": ing["id"],
        "category": "spoilage",
        "quantity": "2.5",
        "unit": "kg",
        "reason": "Left out overnight",
    })
    assert res.status_code == 201
    assert res.json()["category"] == "spoilage"


def test_waste_summary(client, db):
    loc, ing = _setup(client, db)
    now = datetime.now(timezone.utc)

    client.post("/api/waste", json={
        "location_id": loc.id,
        "ingredient_id": ing["id"],
        "category": "spoilage",
        "quantity": "1.0",
        "unit": "kg",
        "cost_estimate": "5.00",
    })
    client.post("/api/waste", json={
        "location_id": loc.id,
        "ingredient_id": ing["id"],
        "category": "trim",
        "quantity": "0.5",
        "unit": "kg",
        "cost_estimate": "2.50",
    })

    date_str = now.strftime("%Y-%m-%dT%H:%M:%S")
    res = client.get(f"/api/waste/summary?location_id={loc.id}&date={date_str}&period=daily")
    assert res.status_code == 200
    data = res.json()
    assert float(data["total_waste_kg"]) == 1.5
    assert float(data["total_waste_cost"]) == 7.50


def test_shelf_life_batch(client, db):
    loc, _ = _setup(client, db)
    recipe = client.post("/api/recipes", json={
        "name": "Hummus", "location_id": loc.id, "base_yield": 20,
    }).json()

    now = datetime.now(timezone.utc)
    expires = (now + timedelta(hours=4)).isoformat()

    res = client.post("/api/batches", json={
        "recipe_id": recipe["id"],
        "location_id": loc.id,
        "expires_at": expires,
        "quantity_produced": 20,
    })
    assert res.status_code == 201
    assert res.json()["quantity_remaining"] == 20
    assert res.json()["status"] == "fresh"
