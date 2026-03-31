"""Tests for the intervention ranking page at /intervenciones."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, TreatmentRecord
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


def _seed_interventions_data(db):
    """Seed farm, field, and treatment records for intervention scoring."""
    farm = Farm(name="Finca Intervenciones", state="Jalisco", total_hectares=30.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela Sur", hectares=10.0,
        crop_type="maiz", planted_at=datetime(2026, 3, 1),
    )
    db.add(field)
    db.flush()
    t1 = TreatmentRecord(
        field_id=field.id, health_score_used=55.0,
        problema="Deficiencia de nitrogeno",
        causa_probable="Suelo agotado despues de cosecha",
        tratamiento="Aplicar composta organica 5 ton/ha",
        costo_estimado_mxn=3500, urgencia="alta",
        prevencion="Rotacion con leguminosas", organic=True,
    )
    t2 = TreatmentRecord(
        field_id=field.id, health_score_used=55.0,
        problema="Estres hidrico",
        causa_probable="Riego insuficiente",
        tratamiento="Aumentar frecuencia de riego",
        costo_estimado_mxn=1500, urgencia="media",
        prevencion="Mulch organico", organic=True,
    )
    db.add_all([t1, t2])
    db.commit()
    return farm, field


# -- Page Load Tests --


class TestIntervencionesPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/intervenciones")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/intervenciones")
        assert "Ranking de Intervenciones" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/intervenciones")
        assert 'id="interv-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/intervenciones")
        assert 'id="interv-field-select"' in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/intervenciones")
        assert 'id="interv-empty"' in resp.text

    def test_page_has_content_container(self, client):
        resp = client.get("/intervenciones")
        assert 'id="interv-content"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/intervenciones")
        assert 'id="interv-stats"' in resp.text

    def test_page_has_cards_grid(self, client):
        resp = client.get("/intervenciones")
        assert 'id="interv-cards"' in resp.text

    def test_page_has_js_script(self, client):
        resp = client.get("/intervenciones")
        assert "intervenciones.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/intervenciones")
        assert "intel-nav" in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/intervenciones")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_load_button(self, client):
        resp = client.get("/intervenciones")
        assert "Ver Ranking" in resp.text


# -- API Integration Tests --


class TestInterventionScoresAPI:
    """Intervention scores API returns expected data."""

    def test_api_returns_scored_treatments(self, client, db):
        farm, field = _seed_interventions_data(db)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/intervention-scores"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_api_scores_sorted_descending(self, client, db):
        farm, field = _seed_interventions_data(db)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/intervention-scores"
        )
        data = resp.json()
        scores = [item["intervention_score"] for item in data]
        assert scores == sorted(scores, reverse=True)

    def test_api_includes_cost_effectiveness(self, client, db):
        farm, field = _seed_interventions_data(db)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/intervention-scores"
        )
        data = resp.json()
        for item in data:
            assert "cost_per_hectare" in item
            assert "intervention_score" in item

    def test_api_empty_field_returns_empty(self, client, db):
        farm = Farm(name="Vacia", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Sin Tratamientos", hectares=5.0, crop_type="frijol")
        db.add(field)
        db.commit()
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/intervention-scores"
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_api_404_for_missing_farm(self, client):
        resp = client.get("/api/farms/9999/fields/1/intervention-scores")
        assert resp.status_code == 404

    def test_api_404_for_missing_field(self, client, db):
        farm = Farm(name="Solo Farm", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/9999/intervention-scores")
        assert resp.status_code == 404
