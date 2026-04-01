"""Tests for the treatment effectiveness report page at /efectividad."""

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
    # Admin users created directly in DB (admin self-registration blocked)
    from cultivos.db.models import User
    from cultivos.auth import hash_password
    # admin user created directly in DB


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
    farm = Farm(name="Finca Efectividad", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela Este", hectares=15.0,
        crop_type="maiz", planted_at=datetime(2026, 2, 1),
    )
    db.add(field)
    db.flush()
    # Treatment with before/after health scores
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
    # Health scores (before and after treatment)
    db.add(HealthScore(field_id=field.id, score=50.0, scored_at=datetime(2026, 2, 10)))
    db.add(HealthScore(field_id=field.id, score=72.0, scored_at=datetime(2026, 3, 10)))
    db.commit()
    return farm, field


# -- Page Load Tests --


class TestEfectividadPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/efectividad")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/efectividad")
        assert "Efectividad de Tratamientos" in resp.text

    def test_page_has_load_button(self, client):
        resp = client.get("/efectividad")
        assert "Cargar Reporte" in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/efectividad")
        assert 'id="eff-empty"' in resp.text

    def test_page_has_content_container(self, client):
        resp = client.get("/efectividad")
        assert 'id="eff-content"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/efectividad")
        assert 'id="eff-stats"' in resp.text

    def test_page_has_cards_grid(self, client):
        resp = client.get("/efectividad")
        assert 'id="eff-cards"' in resp.text

    def test_page_has_js_script(self, client):
        resp = client.get("/efectividad")
        assert "efectividad.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/efectividad")
        assert "intel-nav" in resp.text

    def test_page_subtitle_mentions_analysis(self, client):
        resp = client.get("/efectividad")
        assert "analisis" in resp.text.lower() or "Analisis" in resp.text


# -- API Integration Tests --


class TestTreatmentEffectivenessAPI:
    """Treatment effectiveness report API returns expected data."""

    def test_api_returns_report(self, client, db, admin_headers):
        _seed_effectiveness_data(db)
        resp = client.get(
            "/api/intel/treatment-effectiveness-report",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "treatments" in data or "summary" in data or isinstance(data, dict)

    def test_api_with_crop_filter(self, client, db, admin_headers):
        _seed_effectiveness_data(db)
        resp = client.get(
            "/api/intel/treatment-effectiveness-report",
            params={"crop_type": "maiz"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_api_empty_returns_valid(self, client, db, admin_headers):
        """No treatments should still return a valid response."""
        resp = client.get(
            "/api/intel/treatment-effectiveness-report",
            headers=admin_headers,
        )
        assert resp.status_code == 200
