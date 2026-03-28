"""Tests for farm-level carbon sequestration summary endpoint."""

from datetime import datetime

import pytest

from cultivos.db.models import Farm, Field, SoilAnalysis


@pytest.fixture
def farm_with_soil(db):
    """Farm with two fields, one having soil data with organic_matter_pct."""
    farm = Farm(name="Rancho Carbono", state="Jalisco", total_hectares=40)
    db.add(farm)
    db.flush()

    f1 = Field(farm_id=farm.id, name="Parcela Maiz", crop_type="maiz", hectares=20)
    f2 = Field(farm_id=farm.id, name="Parcela Agave", crop_type="agave", hectares=20)
    db.add_all([f1, f2])
    db.flush()

    db.add(SoilAnalysis(
        field_id=f1.id,
        organic_matter_pct=3.0,
        ph=6.5,
        depth_cm=30.0,
        sampled_at=datetime(2026, 1, 15),
    ))
    db.add(SoilAnalysis(
        field_id=f2.id,
        organic_matter_pct=4.5,
        ph=6.8,
        depth_cm=30.0,
        sampled_at=datetime(2026, 2, 10),
    ))
    db.commit()
    return {"farm_id": farm.id, "field_ids": [f1.id, f2.id]}


@pytest.fixture
def farm_no_soil(db):
    """Farm with fields but no soil data."""
    farm = Farm(name="Rancho Sin Suelo", state="Jalisco", total_hectares=10)
    db.add(farm)
    db.flush()
    f = Field(farm_id=farm.id, name="Parcela Vacia", crop_type="maiz", hectares=10)
    db.add(f)
    db.commit()
    return {"farm_id": farm.id}


@pytest.fixture
def empty_farm(db):
    """Farm with no fields."""
    farm = Farm(name="Rancho Vacio", state="Jalisco", total_hectares=0)
    db.add(farm)
    db.commit()
    return {"farm_id": farm.id}


# -- API integration tests --

def test_farm_carbon_returns_aggregate(client, farm_with_soil):
    """GET /api/farms/{id}/carbon returns aggregated carbon for all fields."""
    fid = farm_with_soil["farm_id"]
    resp = client.get(f"/api/farms/{fid}/carbon")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_fields"] == 2
    assert data["total_hectares"] == 40
    assert data["avg_soc_tonnes_per_ha"] > 0
    assert data["total_co2e_tonnes"] > 0
    assert data["soc_per_ha_rate"] > 0
    assert len(data["fields"]) == 2


def test_farm_carbon_field_entries(client, farm_with_soil):
    """Each field entry has required carbon fields."""
    fid = farm_with_soil["farm_id"]
    resp = client.get(f"/api/farms/{fid}/carbon")
    data = resp.json()
    for entry in data["fields"]:
        assert "field_id" in entry
        assert "field_name" in entry
        assert "soc_tonnes_per_ha" in entry
        assert "clasificacion" in entry
        assert "tendencia" in entry
        assert "co2e_tonnes" in entry


def test_farm_carbon_no_soil_data(client, farm_no_soil):
    """Farm with no soil data returns zero aggregates."""
    fid = farm_no_soil["farm_id"]
    resp = client.get(f"/api/farms/{fid}/carbon")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_fields"] == 0
    assert data["total_co2e_tonnes"] == 0
    assert data["fields"] == []


def test_farm_carbon_empty_farm(client, empty_farm):
    """Farm with no fields returns zero aggregates."""
    fid = empty_farm["farm_id"]
    resp = client.get(f"/api/farms/{fid}/carbon")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_fields"] == 0


def test_farm_carbon_nonexistent_farm(client):
    """Nonexistent farm returns 404."""
    resp = client.get("/api/farms/99999/carbon")
    assert resp.status_code == 404
