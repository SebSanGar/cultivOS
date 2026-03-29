"""Tests for the microbiome health page at /microbioma."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, MicrobiomeRecord
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


def _seed_microbiome_data(db):
    """Seed farm, field, and microbiome records."""
    farm = Farm(name="Rancho Microbioma", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Bio", hectares=12.0, crop_type="maiz")
    db.add(field)
    db.flush()

    records = [
        MicrobiomeRecord(
            field_id=field.id,
            respiration_rate=55.0,
            microbial_biomass_carbon=320.0,
            fungi_bacteria_ratio=1.8,
            classification="healthy",
            sampled_at=datetime(2026, 1, 15),
        ),
        MicrobiomeRecord(
            field_id=field.id,
            respiration_rate=35.0,
            microbial_biomass_carbon=210.0,
            fungi_bacteria_ratio=1.2,
            classification="moderate",
            sampled_at=datetime(2026, 2, 15),
        ),
        MicrobiomeRecord(
            field_id=field.id,
            respiration_rate=15.0,
            microbial_biomass_carbon=90.0,
            fungi_bacteria_ratio=0.5,
            classification="degraded",
            sampled_at=datetime(2026, 3, 15),
        ),
    ]
    db.add_all(records)
    db.commit()
    return farm, field


class TestMicrobiomePageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/microbioma")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/microbioma")
        assert "Microbioma" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/microbioma")
        assert 'id="micro-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/microbioma")
        assert 'id="micro-field-select"' in resp.text

    def test_page_has_chart_canvas(self, client):
        resp = client.get("/microbioma")
        assert 'id="micro-respiration-chart"' in resp.text

    def test_page_has_ratio_chart(self, client):
        resp = client.get("/microbioma")
        assert 'id="micro-ratio-chart"' in resp.text

    def test_page_has_data_table(self, client):
        resp = client.get("/microbioma")
        assert 'id="micro-table-body"' in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/microbioma")
        assert 'id="micro-empty"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/microbioma")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/microbioma")
        assert "microbiome.js" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/microbioma")
        html = resp.text
        assert 'id="micro-avg-respiration"' in html
        assert 'id="micro-avg-ratio"' in html
        assert 'id="micro-record-count"' in html

    def test_page_has_nav_link(self, client):
        resp = client.get("/microbioma")
        assert "/microbioma" in resp.text


class TestMicrobiomeAPI:
    """Microbiome API returns expected data with seeded records."""

    def test_microbiome_records_returned(self, client, db):
        farm, field = _seed_microbiome_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/microbiome")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    def test_microbiome_record_fields(self, client, db):
        farm, field = _seed_microbiome_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/microbiome")
        data = resp.json()
        rec = data[0]
        assert "respiration_rate" in rec
        assert "microbial_biomass_carbon" in rec
        assert "fungi_bacteria_ratio" in rec
        assert "classification" in rec

    def test_microbiome_classification_values(self, client, db):
        farm, field = _seed_microbiome_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/microbiome")
        data = resp.json()
        classifications = {r["classification"] for r in data}
        assert "healthy" in classifications
        assert "degraded" in classifications

    def test_empty_microbiome_for_new_field(self, client, db):
        farm = Farm(name="Rancho Vacio", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Campo Nuevo", hectares=3.0, crop_type="frijol")
        db.add(field)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/microbiome")
        data = resp.json()
        assert len(data) == 0


class TestMicrobiomePageContent:
    """Page HTML has correct structure for microbiome data rendering."""

    def test_page_has_respiration_section(self, client):
        resp = client.get("/microbioma")
        html = resp.text.lower()
        assert "respiracion" in html or "respiration" in html

    def test_page_has_biomass_label(self, client):
        resp = client.get("/microbioma")
        html = resp.text.lower()
        assert "biomasa" in html or "carbono" in html

    def test_page_has_classification_legend(self, client):
        resp = client.get("/microbioma")
        html = resp.text.lower()
        assert "saludable" in html or "moderado" in html or "degradado" in html
