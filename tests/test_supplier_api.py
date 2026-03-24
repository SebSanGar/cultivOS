"""Integration tests for supplier and pricing API."""

from cultivos.db.models import Location


def _setup(db):
    loc = Location(name="Test Kitchen", timezone="America/Toronto")
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


def test_create_supplier(client, db):
    loc = _setup(db)
    res = client.post("/api/suppliers", json={
        "name": "Fresh Farms",
        "location_id": loc.id,
        "categories": ["produce", "dairy"],
        "payment_terms": "net_30",
    })
    assert res.status_code == 201
    assert res.json()["name"] == "Fresh Farms"
    assert res.json()["categories"] == ["produce", "dairy"]


def test_log_price(client, db):
    loc = _setup(db)
    sup = client.post("/api/suppliers", json={"name": "S1", "location_id": loc.id}).json()
    ing = client.post("/api/ingredients", json={"name": "Chicken", "location_id": loc.id}).json()

    res = client.post("/api/prices", json={
        "ingredient_id": ing["id"],
        "supplier_id": sup["id"],
        "price_per_unit": "12.50",
        "unit": "kg",
    })
    assert res.status_code == 201
    assert float(res.json()["price_per_unit"]) == 12.50


def test_price_comparison(client, db):
    loc = _setup(db)
    s1 = client.post("/api/suppliers", json={"name": "Cheap", "location_id": loc.id}).json()
    s2 = client.post("/api/suppliers", json={"name": "Expensive", "location_id": loc.id}).json()
    ing = client.post("/api/ingredients", json={"name": "Salmon", "location_id": loc.id}).json()

    client.post("/api/prices", json={
        "ingredient_id": ing["id"], "supplier_id": s1["id"],
        "price_per_unit": "20.00", "unit": "kg",
    })
    client.post("/api/prices", json={
        "ingredient_id": ing["id"], "supplier_id": s2["id"],
        "price_per_unit": "28.00", "unit": "kg",
    })

    res = client.get(f"/api/ingredients/{ing['id']}/compare")
    assert res.status_code == 200
    data = res.json()
    assert len(data["prices"]) == 2
    # Cheapest first
    assert float(data["prices"][0]["price_per_unit"]) == 20.00
