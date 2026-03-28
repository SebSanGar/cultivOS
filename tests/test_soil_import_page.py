"""Tests for /importar-suelo — soil data CSV import page."""

import io

from cultivos.db.models import Farm, Field, SoilAnalysis


class TestSoilImportPageRoute:
    """Soil import page serves and contains expected elements."""

    def test_route_returns_200(self, client):
        resp = client.get("/importar-suelo")
        assert resp.status_code == 200

    def test_route_returns_html(self, client):
        resp = client.get("/importar-suelo")
        assert "text/html" in resp.headers.get("content-type", "")

    def test_page_contains_title(self, client):
        resp = client.get("/importar-suelo")
        assert "Importar Datos de Suelo" in resp.text

    def test_page_has_nav_with_links(self, client):
        resp = client.get("/importar-suelo")
        body = resp.text
        assert 'href="/"' in body
        assert 'href="/intel"' in body

    def test_page_loads_soil_import_js(self, client):
        resp = client.get("/importar-suelo")
        assert "soil-import.js" in resp.text


class TestSoilImportPageElements:
    """Page contains required form elements for CSV upload."""

    def test_page_contains_farm_selector(self, client):
        resp = client.get("/importar-suelo")
        assert "si-farm-select" in resp.text

    def test_page_contains_field_selector(self, client):
        resp = client.get("/importar-suelo")
        assert "si-field-select" in resp.text

    def test_page_contains_file_picker(self, client):
        resp = client.get("/importar-suelo")
        body = resp.text
        assert 'type="file"' in body
        assert ".csv" in body

    def test_page_contains_preview_table(self, client):
        resp = client.get("/importar-suelo")
        assert "si-preview-table" in resp.text

    def test_page_contains_import_button(self, client):
        resp = client.get("/importar-suelo")
        assert "si-import-btn" in resp.text

    def test_page_contains_results_section(self, client):
        resp = client.get("/importar-suelo")
        assert "si-results" in resp.text

    def test_page_contains_error_section(self, client):
        resp = client.get("/importar-suelo")
        assert "si-errors" in resp.text

    def test_page_contains_spanish_labels(self, client):
        resp = client.get("/importar-suelo")
        body = resp.text
        assert "Granja" in body
        assert "Parcela" in body
        assert "Archivo CSV" in body


class TestSoilImportCSVEndpoint:
    """CSV upload endpoint works via the existing API."""

    def test_import_valid_csv(self, client, db):
        farm = Farm(name="Test", state="Jalisco", total_hectares=10)
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(name="Lote A", farm_id=farm.id, crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)

        csv_data = "sampled_at,ph,organic_matter_pct,nitrogen_ppm\n2025-06-15,6.8,3.2,45\n2025-07-20,7.1,2.9,38\n"
        resp = client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/soil/import-csv",
            files={"file": ("soil.csv", io.BytesIO(csv_data.encode()), "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 2
        assert data["skipped"] == 0

    def test_import_csv_missing_required_column(self, client, db):
        farm = Farm(name="Test", state="Jalisco", total_hectares=10)
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(name="Lote A", farm_id=farm.id, crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)

        csv_data = "ph,organic_matter_pct\n6.8,3.2\n"
        resp = client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/soil/import-csv",
            files={"file": ("soil.csv", io.BytesIO(csv_data.encode()), "text/csv")},
        )
        assert resp.status_code == 422

    def test_import_csv_duplicate_detection(self, client, db):
        farm = Farm(name="Test", state="Jalisco", total_hectares=10)
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(name="Lote A", farm_id=farm.id, crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)

        csv_data = "sampled_at,ph\n2025-06-15,6.8\n"
        # Import once
        client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/soil/import-csv",
            files={"file": ("soil.csv", io.BytesIO(csv_data.encode()), "text/csv")},
        )
        # Import again — should skip duplicate
        resp = client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/soil/import-csv",
            files={"file": ("soil.csv", io.BytesIO(csv_data.encode()), "text/csv")},
        )
        data = resp.json()
        assert data["imported"] == 0
        assert data["skipped"] == 1

    def test_import_csv_invalid_farm(self, client, db):
        resp = client.post(
            "/api/farms/999/fields/999/soil/import-csv",
            files={"file": ("soil.csv", io.BytesIO(b"sampled_at\n2025-01-01\n"), "text/csv")},
        )
        assert resp.status_code == 404
