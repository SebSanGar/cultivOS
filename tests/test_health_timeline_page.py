"""Tests for the field health history timeline page at /historial."""

import pytest
from datetime import datetime
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


def _seed_farm_with_history(db):
    """Seed a farm with fields, health scores, and applied treatments."""
    farm = Farm(name="Rancho Timeline", state="Jalisco", total_hectares=15.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Maiz Norte", hectares=10.0, crop_type="maiz")
    db.add(field)
    db.flush()
    # Health scores over time
    hs1 = HealthScore(
        field_id=field.id, score=55.0, scored_at=datetime(2026, 1, 15),
        trend="declining", sources=["ndvi"], breakdown={"ndvi": 55.0},
    )
    hs2 = HealthScore(
        field_id=field.id, score=62.0, scored_at=datetime(2026, 2, 1),
        trend="improving", sources=["ndvi", "soil"], breakdown={"ndvi": 60.0, "soil": 64.0},
    )
    hs3 = HealthScore(
        field_id=field.id, score=70.0, scored_at=datetime(2026, 2, 15),
        trend="improving", sources=["ndvi"], breakdown={"ndvi": 70.0},
    )
    hs4 = HealthScore(
        field_id=field.id, score=75.0, scored_at=datetime(2026, 3, 1),
        trend="improving", sources=["ndvi", "soil"], breakdown={"ndvi": 73.0, "soil": 77.0},
    )
    db.add_all([hs1, hs2, hs3, hs4])
    db.flush()
    # Applied treatment
    tr = TreatmentRecord(
        field_id=field.id,
        problema="Deficiencia de nitrogeno",
        causa_probable="Suelo agotado por monocultivo",
        tratamiento="Composta organica",
        prevencion="Rotacion de cultivos cada temporada",
        urgencia="media",
        organic=True,
        health_score_used=55.0,
        applied_at=datetime(2026, 1, 20),
        applied_notes="Aplicado en parcela norte",
        created_at=datetime(2026, 1, 16),
    )
    db.add(tr)
    db.commit()
    return farm, field


class TestTimelinePageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/historial")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/historial")
        assert "Historial" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/historial")
        assert 'id="tl-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/historial")
        assert 'id="tl-field-select"' in resp.text

    def test_page_has_timeline_container(self, client):
        resp = client.get("/historial")
        assert 'id="tl-timeline"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/historial")
        html = resp.text
        assert 'id="tl-score-count"' in html
        assert 'id="tl-trend"' in html
        assert 'id="tl-treatment-count"' in html

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/historial")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html


class TestTimelineAPIs:
    """Health history and treatment history APIs return expected data."""

    def test_health_history_returns_scores(self, client, db):
        farm, field = _seed_farm_with_history(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 4
        assert len(data["scores"]) == 4
        # Sorted chronologically (oldest first)
        dates = [s["scored_at"] for s in data["scores"]]
        assert dates == sorted(dates)

    def test_health_history_has_trend(self, client, db):
        farm, field = _seed_farm_with_history(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health/history")
        data = resp.json()
        assert data["trend"] in ("improving", "stable", "declining", "insufficient_data")

    def test_treatment_history_returns_applied(self, client, db):
        farm, field = _seed_farm_with_history(db)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/treatments/treatment-history"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["tratamiento"] == "Composta organica"
        assert data[0]["applied_at"] is not None

    def test_treatment_history_has_outcome_fields(self, client, db):
        farm, field = _seed_farm_with_history(db)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/treatments/treatment-history"
        )
        data = resp.json()
        entry = data[0]
        assert "problema" in entry
        assert "urgencia" in entry
        assert "health_score_used" in entry


class TestTimelinePageContent:
    """Page HTML has correct structure for timeline rendering."""

    def test_page_has_js_script(self, client):
        resp = client.get("/historial")
        assert "timeline.js" in resp.text

    def test_page_has_legend(self, client):
        resp = client.get("/historial")
        html = resp.text
        assert "Salud" in html or "Puntuaci" in html
        assert "Tratamiento" in html

    def test_page_has_empty_state(self, client):
        resp = client.get("/historial")
        assert 'id="tl-empty"' in resp.text
