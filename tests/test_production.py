"""Tests for production scheduling and demand forecasting."""

from decimal import Decimal

from cultivos.services.demand_service import (
    calculate_safety_buffer,
    recommend_par,
    simple_moving_average,
    standard_deviation,
)
from cultivos.db.models import Location


class TestDemandService:
    def test_safety_buffer(self):
        result = calculate_safety_buffer(Decimal("12"), Decimal("1.3"))
        assert result == 16  # ceil(12 * 1.3) = ceil(15.6) = 16

    def test_par_recommendation(self):
        rec = recommend_par(1, Decimal("40"), Decimal("12"))
        assert rec.recommended_base_par == 40
        assert rec.recommended_safety_buffer == 16
        assert rec.recommended_effective_par == 56

    def test_simple_moving_average(self):
        values = [30, 35, 40, 45, 50, 55, 60]
        avg = simple_moving_average(values, window=7)
        assert avg == Decimal("45.00")

    def test_standard_deviation(self):
        values = [40, 42, 38, 44, 36]
        sd = standard_deviation(values)
        assert sd > Decimal("2")
        assert sd < Decimal("4")

    def test_empty_values(self):
        assert simple_moving_average([]) == Decimal("0")
        assert standard_deviation([]) == Decimal("0")


def test_par_level_api(client, db):
    loc = Location(name="Test Kitchen", timezone="America/Toronto")
    db.add(loc)
    db.commit()
    db.refresh(loc)

    recipe = client.post("/api/recipes", json={
        "name": "Soup", "location_id": loc.id, "base_yield": 10,
    }).json()

    res = client.post("/api/par-levels", json={
        "recipe_id": recipe["id"],
        "location_id": loc.id,
        "base_par": 40,
        "safety_buffer": 16,
    })
    assert res.status_code == 201
    assert res.json()["effective_par"] == 56


def test_production_needs(client, db):
    loc = Location(name="Test Kitchen", timezone="America/Toronto")
    db.add(loc)
    db.commit()
    db.refresh(loc)

    recipe = client.post("/api/recipes", json={
        "name": "Salad", "location_id": loc.id, "base_yield": 1,
    }).json()

    # Set par level
    client.post("/api/par-levels", json={
        "recipe_id": recipe["id"],
        "location_id": loc.id,
        "base_par": 30,
        "safety_buffer": 10,
    })

    # No batches = need everything
    res = client.get(f"/api/production/needs?location_id={loc.id}")
    assert res.status_code == 200
    needs = res.json()
    assert len(needs) == 1
    assert needs[0]["needed"] == 40  # effective_par = 30 + 10
    assert needs[0]["current_stock"] == 0
