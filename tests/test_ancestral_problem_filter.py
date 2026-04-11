"""Tests for ancestral method filtering by problem and crop — task #123."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import AncestralMethod
from cultivos.db.session import get_db


@pytest.fixture()
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    # Seed two ancestral methods with different problems/crops
    m1 = AncestralMethod(
        name="Milpa Test",
        description_es="Policultivo mesoamericano",
        region="Jalisco",
        practice_type="intercropping",
        crops=["maiz", "frijol", "calabaza"],
        benefits_es="Fijacion de nitrogeno, control de malezas",
        scientific_basis=None,
        problems=["nitrogen_deficiency", "weed_competition"],
    )
    m2 = AncestralMethod(
        name="Terrazas Test",
        description_es="Plataformas escalonadas",
        region="Jalisco",
        practice_type="soil_management",
        crops=["maiz", "agave"],
        benefits_es="Prevencion de erosion",
        scientific_basis=None,
        problems=["erosion", "compaction"],
    )
    m3 = AncestralMethod(
        name="Chinampa Test",
        description_es="Islas flotantes",
        region="Valle de Mexico",
        practice_type="water_management",
        crops=["maiz", "chile", "tomate"],
        benefits_es="Productividad alta",
        scientific_basis=None,
        problems=["drought", "waterlogging"],
    )
    db.add_all([m1, m2, m3])
    db.commit()

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def test_problem_filter_returns_matching_methods(client):
    """GET /api/knowledge/ancestral?problem=erosion should return methods with erosion in problems."""
    resp = client.get("/api/knowledge/ancestral?problem=erosion")
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()]
    assert "Terrazas Test" in names
    assert "Milpa Test" not in names


def test_crop_filter_returns_matching_methods(client):
    """GET /api/knowledge/ancestral?crop=agave should return methods with agave in crops."""
    resp = client.get("/api/knowledge/ancestral?crop=agave")
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()]
    assert "Terrazas Test" in names
    assert "Chinampa Test" not in names


def test_combined_problem_and_crop_filter(client):
    """problem=nitrogen_deficiency&crop=maiz should return Milpa only."""
    resp = client.get("/api/knowledge/ancestral?problem=nitrogen_deficiency&crop=maiz")
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()]
    assert names == ["Milpa Test"]


def test_unknown_problem_returns_empty_list(client):
    """Unknown problem → 200 with empty list, not 404."""
    resp = client.get("/api/knowledge/ancestral?problem=unknown_nonexistent_problem")
    assert resp.status_code == 200
    assert resp.json() == []


def test_maiz_only_filter(client):
    """crop=maiz returns all methods that include maiz."""
    resp = client.get("/api/knowledge/ancestral?crop=maiz")
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()]
    assert "Milpa Test" in names
    assert "Terrazas Test" in names
    assert "Chinampa Test" in names


def test_no_filter_returns_all(client):
    """No params → returns all 3 seeded methods."""
    resp = client.get("/api/knowledge/ancestral")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_problems_included_in_response(client):
    """Response includes problems list for each method."""
    resp = client.get("/api/knowledge/ancestral?problem=compaction")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "problems" in data[0]
    assert "compaction" in data[0]["problems"]


def test_problem_filter_case_insensitive(client):
    """problem filter should be case-insensitive."""
    resp = client.get("/api/knowledge/ancestral?problem=EROSION")
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()]
    assert "Terrazas Test" in names


def test_crop_filter_case_insensitive(client):
    """crop filter should be case-insensitive."""
    resp = client.get("/api/knowledge/ancestral?crop=AGAVE")
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()]
    assert "Terrazas Test" in names
