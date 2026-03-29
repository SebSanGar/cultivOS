"""Tests for the anomaly detection center page at /anomalias."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, HealthScore, NDVIResult
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


def _seed_anomaly_data(db):
    """Seed farm, field, and health/NDVI data with anomalies (drops)."""
    farm = Farm(name="Rancho Alerta", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Norte", hectares=12.0, crop_type="maiz")
    db.add(field)
    db.flush()

    # Health scores with a >15 point drop (anomaly)
    scores = [
        HealthScore(field_id=field.id, score=80.0, scored_at=datetime(2026, 1, 10)),
        HealthScore(field_id=field.id, score=60.0, scored_at=datetime(2026, 2, 10)),  # -20 drop
        HealthScore(field_id=field.id, score=55.0, scored_at=datetime(2026, 3, 10)),
    ]
    db.add_all(scores)

    # NDVI with a >20% drop from average (anomaly)
    ndvi_base = dict(ndvi_std=0.1, pixels_total=1000, stress_pct=5.0, zones=[])
    ndvis = [
        NDVIResult(field_id=field.id, ndvi_mean=0.70, ndvi_min=0.50, ndvi_max=0.85, analyzed_at=datetime(2026, 1, 5), **ndvi_base),
        NDVIResult(field_id=field.id, ndvi_mean=0.72, ndvi_min=0.52, ndvi_max=0.87, analyzed_at=datetime(2026, 2, 5), **ndvi_base),
        NDVIResult(field_id=field.id, ndvi_mean=0.40, ndvi_min=0.20, ndvi_max=0.55, analyzed_at=datetime(2026, 3, 5), **ndvi_base),  # big drop
    ]
    db.add_all(ndvis)
    db.commit()
    return farm, field


class TestAnomaliesPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/anomalias")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/anomalias")
        assert "Anomal" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/anomalias")
        assert 'id="anom-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/anomalias")
        assert 'id="anom-field-select"' in resp.text

    def test_page_has_anomaly_container(self, client):
        resp = client.get("/anomalias")
        assert 'id="anom-timeline"' in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/anomalias")
        assert 'id="anom-empty"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/anomalias")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/anomalias")
        assert "anomalies.js" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/anomalias")
        html = resp.text
        assert 'id="anom-health-count"' in html
        assert 'id="anom-ndvi-count"' in html
        assert 'id="anom-total-count"' in html

    def test_page_has_severity_legend(self, client):
        resp = client.get("/anomalias")
        html = resp.text
        assert "Critica" in html or "critica" in html or "Cr" in html
        assert "Moderada" in html or "moderada" in html

    def test_page_has_nav_link(self, client):
        resp = client.get("/anomalias")
        assert "/anomalias" in resp.text


class TestAnomaliesAPI:
    """Anomaly API returns expected data with seeded anomalies."""

    def test_anomalies_endpoint_returns_data(self, client, db):
        farm, field = _seed_anomaly_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/anomalies")
        assert resp.status_code == 200
        data = resp.json()
        assert "health_anomalies" in data
        assert "ndvi_anomalies" in data

    def test_health_anomaly_detected(self, client, db):
        farm, field = _seed_anomaly_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/anomalies")
        data = resp.json()
        assert len(data["health_anomalies"]) >= 1
        ha = data["health_anomalies"][0]
        assert ha["drop"] >= 15
        assert "recommendation" in ha

    def test_ndvi_anomaly_detected(self, client, db):
        farm, field = _seed_anomaly_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/anomalies")
        data = resp.json()
        assert len(data["ndvi_anomalies"]) >= 1
        na = data["ndvi_anomalies"][0]
        assert na["drop_pct"] >= 20
        assert "recommendation" in na

    def test_no_anomalies_for_stable_field(self, client, db):
        farm = Farm(name="Rancho Estable", state="Jalisco", total_hectares=20.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Campo Estable", hectares=5.0, crop_type="frijol")
        db.add(field)
        db.flush()
        # Stable scores - no drops
        scores = [
            HealthScore(field_id=field.id, score=70.0, scored_at=datetime(2026, 1, 1)),
            HealthScore(field_id=field.id, score=72.0, scored_at=datetime(2026, 2, 1)),
        ]
        db.add_all(scores)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/anomalies")
        data = resp.json()
        assert len(data["health_anomalies"]) == 0


class TestAnomaliesPageContent:
    """Page HTML has correct structure for anomaly rendering."""

    def test_page_has_health_section(self, client):
        resp = client.get("/anomalias")
        assert "Salud" in resp.text or "salud" in resp.text

    def test_page_has_ndvi_section(self, client):
        resp = client.get("/anomalias")
        assert "NDVI" in resp.text

    def test_page_has_recommendation_area(self, client):
        resp = client.get("/anomalias")
        assert "recomendacion" in resp.text.lower() or "Recomendacion" in resp.text
