"""Tests for crop variety search endpoint — task #166."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import CropVariety
from cultivos.db.session import get_db


@pytest.fixture()
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    # Seed varieties across two crops and regions/altitudes
    db.add_all([
        CropVariety(
            crop_name="maiz",
            name="Maiz Azul Criollo Search",
            region="Altos de Jalisco",
            altitude_m=1800,
            water_mm=700,
            diseases=[],
            adaptation_notes="Alta resistencia a sequia",
        ),
        CropVariety(
            crop_name="maiz",
            name="Maiz Blanco Temporal Search",
            region="Valles Centrales",
            altitude_m=1500,
            water_mm=650,
            diseases=[],
            adaptation_notes="Ciclo corto",
        ),
        CropVariety(
            crop_name="maiz",
            name="Maiz Morado Costa Search",
            region="Costa Sur de Jalisco",
            altitude_m=300,
            water_mm=900,
            diseases=[],
            adaptation_notes="Tolerante a humedad",
        ),
        CropVariety(
            crop_name="agave",
            name="Agave Azul Tequilana Search",
            region="Jalisco",
            altitude_m=1200,
            water_mm=800,
            diseases=[],
            adaptation_notes="Variedad oficial tequila",
        ),
    ])
    db.commit()

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def test_crop_filter_returns_all_for_crop(client):
    """GET /api/knowledge/crop-varieties?crop=maiz returns all maiz varieties."""
    resp = client.get("/api/knowledge/crop-varieties", params={"crop": "maiz"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    for v in data:
        assert v["crop_name"] == "maiz"


def test_unknown_crop_returns_empty_list(client):
    """Unknown crop returns 200 with empty list — not 404."""
    resp = client.get("/api/knowledge/crop-varieties", params={"crop": "zanahoria"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_region_filter_narrows_results(client):
    """region=Altos returns only the Altos de Jalisco variety."""
    resp = client.get("/api/knowledge/crop-varieties", params={"crop": "maiz", "region": "Altos"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Maiz Azul Criollo Search"


def test_altitude_filter_within_500m(client):
    """altitude_m=1600 should return varieties within ±500m (1100-2100m)."""
    # altitude_m=1600 → filter: 1100 to 2100
    # Altos (1800m): within range ✓
    # Temporal (1500m): within range ✓
    # Costa (300m): out of range ✗
    resp = client.get("/api/knowledge/crop-varieties", params={"crop": "maiz", "altitude_m": 1600})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = [v["name"] for v in data]
    assert "Maiz Azul Criollo Search" in names
    assert "Maiz Blanco Temporal Search" in names
    assert "Maiz Morado Costa Search" not in names


def test_both_filters_intersection(client):
    """region=Altos AND altitude_m=1700 → only the Altos variety (1800m in range)."""
    resp = client.get("/api/knowledge/crop-varieties", params={
        "crop": "maiz",
        "region": "Altos",
        "altitude_m": 1700,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Maiz Azul Criollo Search"


def test_sorted_by_water_mm_asc(client):
    """Results sorted by water_mm ASC — most drought-efficient first."""
    resp = client.get("/api/knowledge/crop-varieties", params={"crop": "maiz"})
    assert resp.status_code == 200
    data = resp.json()
    water_values = [v["water_mm"] for v in data if v["water_mm"] is not None]
    assert water_values == sorted(water_values)


def test_region_filter_case_insensitive(client):
    """Region filter is case-insensitive: 'altos' matches 'Altos de Jalisco'."""
    resp = client.get("/api/knowledge/crop-varieties", params={"crop": "maiz", "region": "altos"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Maiz Azul Criollo Search"


def test_required_fields_in_response(client):
    """Response items include all required fields."""
    resp = client.get("/api/knowledge/crop-varieties", params={"crop": "agave"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    v = data[0]
    assert "name" in v
    assert "region" in v
    assert "altitude_m" in v
    assert "water_mm" in v
    assert "crop_name" in v
