"""Tests for the global treatment effectiveness dashboard at /efectividad-global."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
from cultivos.db.session import get_db


@pytest.fixture()
def app(db):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def admin_headers(client, db):
    """Register admin user and return auth headers."""
    from cultivos.db.models import User
    from cultivos.auth import hash_password

    if not db.query(User).filter(User.username == "testadmin").first():
        db.add(User(username="testadmin", hashed_password=hash_password("secret123"), role="admin"))
        db.commit()
    resp = client.post("/api/auth/login", json={
        "username": "testadmin", "password": "secret123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_effectiveness_data(db):
    """Seed farm, field, treatments with health scores for effectiveness reporting."""
    farm = Farm(name="Finca Global", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela Norte", hectares=15.0,
        crop_type="maiz", planted_at=datetime(2026, 2, 1),
    )
    db.add(field)
    db.flush()
    t = TreatmentRecord(
        field_id=field.id, health_score_used=50.0,
        problema="Bajo vigor",
        causa_probable="Suelo compactado",
        tratamiento="Composta organica 3 ton/ha",
        costo_estimado_mxn=2500, urgencia="media",
        prevencion="Rotacion de cultivos", organic=True,
        applied_at=datetime(2026, 2, 15),
    )
    db.add(t)
    db.add(HealthScore(field_id=field.id, score=50.0, scored_at=datetime(2026, 2, 10)))
    db.add(HealthScore(field_id=field.id, score=72.0, scored_at=datetime(2026, 3, 10)))
    db.commit()
    return farm, field


# -- Page Load Tests --


class TestEfectividadGlobalPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/efectividad-global")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/efectividad-global")
        assert "Efectividad Global" in resp.text

    def test_page_has_chart_container(self, client):
        resp = client.get("/efectividad-global")
        assert 'id="effg-chart-container"' in resp.text

    def test_page_has_canvas_for_chart(self, client):
        resp = client.get("/efectividad-global")
        assert 'id="effg-bar-chart"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/efectividad-global")
        assert 'id="effg-stats"' in resp.text

    def test_page_has_crop_filter(self, client):
        resp = client.get("/efectividad-global")
        assert 'id="effg-crop-filter"' in resp.text

    def test_page_has_region_filter(self, client):
        resp = client.get("/efectividad-global")
        assert 'id="effg-region-filter"' in resp.text

    def test_page_has_cards_container(self, client):
        resp = client.get("/efectividad-global")
        assert 'id="effg-cards"' in resp.text

    def test_page_has_js_script(self, client):
        resp = client.get("/efectividad-global")
        assert "efectividad-global.js" in resp.text

    def test_page_has_chartjs_cdn(self, client):
        resp = client.get("/efectividad-global")
        assert "chart.js" in resp.text.lower() or "chart.umd" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/efectividad-global")
        assert "intel-nav" in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/efectividad-global")
        assert 'id="effg-empty"' in resp.text

    def test_page_subtitle(self, client):
        resp = client.get("/efectividad-global")
        assert "salud" in resp.text.lower() or "tratamiento" in resp.text.lower()

    def test_page_has_footer(self, client):
        resp = client.get("/efectividad-global")
        assert "cultivos-footer" in resp.text


# -- API Integration Tests --


class TestEfectividadGlobalAPI:
    """Treatment effectiveness report API works with filters."""

    def test_api_returns_report(self, client, db, admin_headers):
        _seed_effectiveness_data(db)
        resp = client.get(
            "/api/intel/treatment-effectiveness-report",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "treatments" in data

    def test_api_with_crop_filter(self, client, db, admin_headers):
        _seed_effectiveness_data(db)
        resp = client.get(
            "/api/intel/treatment-effectiveness-report",
            params={"crop_type": "maiz"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "treatments" in data

    def test_api_treatments_have_expected_fields(self, client, db, admin_headers):
        _seed_effectiveness_data(db)
        resp = client.get(
            "/api/intel/treatment-effectiveness-report",
            headers=admin_headers,
        )
        data = resp.json()
        if data["treatments"]:
            t = data["treatments"][0]
            assert "tratamiento" in t
            assert "total_applications" in t
            assert "composite_score" in t

    def test_api_empty_returns_valid(self, client, db, admin_headers):
        resp = client.get(
            "/api/intel/treatment-effectiveness-report",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "treatments" in data
        assert isinstance(data["treatments"], list)
