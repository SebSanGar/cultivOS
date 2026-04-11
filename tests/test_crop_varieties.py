"""Tests for Jalisco/LATAM crop variety knowledge base — task #126."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import CropVariety
from cultivos.db.session import get_db


@pytest.fixture()
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    # Seed three varieties across two crops
    db.add_all([
        CropVariety(
            crop_name="maiz",
            name="Maiz Azul Criollo Test",
            region="Altos de Jalisco",
            altitude_m=1800,
            water_mm=700,
            diseases=["tizón_foliar", "carbón"],
            adaptation_notes="Resistente a sequía moderada",
        ),
        CropVariety(
            crop_name="maiz",
            name="Maiz Blanco de Temporal Test",
            region="Valles Centrales de Jalisco",
            altitude_m=1500,
            water_mm=650,
            diseases=["roya"],
            adaptation_notes="Ciclo corto, ideal para temporal",
        ),
        CropVariety(
            crop_name="agave",
            name="Agave Azul Tequilana Test",
            region="Jalisco",
            altitude_m=1200,
            water_mm=800,
            diseases=["pudrición_de_raíz"],
            adaptation_notes="Variedad oficial para tequila DO",
        ),
    ])
    db.commit()

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def test_known_crop_returns_varieties(client):
    """GET /api/knowledge/crops/maiz/varieties returns the two seeded maiz varieties."""
    resp = client.get("/api/knowledge/crops/maiz/varieties")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = [v["name"] for v in data]
    assert "Maiz Azul Criollo Test" in names
    assert "Maiz Blanco de Temporal Test" in names


def test_unknown_crop_returns_404(client):
    """GET /api/knowledge/crops/zanahoria/varieties → 404."""
    resp = client.get("/api/knowledge/crops/zanahoria/varieties")
    assert resp.status_code == 404


def test_variety_fields_present(client):
    """Response includes all required fields: name, region, altitude_m, water_mm, diseases."""
    resp = client.get("/api/knowledge/crops/maiz/varieties")
    assert resp.status_code == 200
    variety = resp.json()[0]
    assert "name" in variety
    assert "region" in variety
    assert "altitude_m" in variety
    assert "water_mm" in variety
    assert "diseases" in variety
    assert isinstance(variety["diseases"], list)


def test_agave_variety_returned(client):
    """GET /api/knowledge/crops/agave/varieties returns agave variety."""
    resp = client.get("/api/knowledge/crops/agave/varieties")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Agave Azul Tequilana Test"


def test_variety_values_correct(client):
    """Altitude, water_mm, and diseases values are returned accurately."""
    resp = client.get("/api/knowledge/crops/agave/varieties")
    assert resp.status_code == 200
    v = resp.json()[0]
    assert v["altitude_m"] == 1200
    assert v["water_mm"] == 800
    assert "pudrición_de_raíz" in v["diseases"]


def test_crop_name_case_insensitive(client):
    """GET /api/knowledge/crops/MAIZ/varieties (uppercase) → same result."""
    resp = client.get("/api/knowledge/crops/MAIZ/varieties")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_crop_with_no_varieties_returns_404(client):
    """A crop that exists in general but has no varieties seeded → 404."""
    resp = client.get("/api/knowledge/crops/frijol/varieties")
    assert resp.status_code == 404


def test_adaptation_notes_present(client):
    """adaptation_notes field is returned in response."""
    resp = client.get("/api/knowledge/crops/maiz/varieties")
    assert resp.status_code == 200
    v = resp.json()[0]
    assert "adaptation_notes" in v
