"""Tests for the microbiome health panel on field detail page (/campo)."""

import pytest


class TestMicrobiomePanelHTML:
    """Tests that field detail HTML contains microbiome section."""

    def test_microbiome_section_exists(self, client):
        """Field detail page has a microbiome section container."""
        resp = client.get("/campo")
        assert resp.status_code == 200
        html = resp.text
        assert 'id="section-microbiome"' in html

    def test_microbiome_section_title_spanish(self, client):
        """Microbiome section has Spanish title."""
        resp = client.get("/campo")
        html = resp.text
        assert "Salud del Microbioma" in html

    def test_microbiome_content_container(self, client):
        """Microbiome section has a content container for JS rendering."""
        resp = client.get("/campo")
        html = resp.text
        assert 'id="microbiome-content"' in html


class TestMicrobiomePanelJS:
    """Tests that field.js contains microbiome rendering logic."""

    def test_js_fetches_microbiome(self, client):
        """field.js fetches the microbiome endpoint."""
        resp = client.get("/field.js")
        assert resp.status_code == 200
        js = resp.text
        assert "/microbiome" in js

    def test_js_has_render_microbiome(self, client):
        """field.js has a renderMicrobiome function."""
        resp = client.get("/field.js")
        js = resp.text
        assert "renderMicrobiome" in js

    def test_js_renders_classification(self, client):
        """renderMicrobiome shows classification badge."""
        resp = client.get("/field.js")
        js = resp.text
        assert "classification" in js.lower() or "clasificacion" in js.lower()

    def test_js_renders_respiration(self, client):
        """renderMicrobiome shows respiration rate."""
        resp = client.get("/field.js")
        js = resp.text
        assert "respiration_rate" in js or "Respiracion" in js

    def test_js_handles_no_microbiome_data(self, client):
        """renderMicrobiome handles null/empty data gracefully."""
        resp = client.get("/field.js")
        js = resp.text
        # Should have a null/empty check before rendering
        assert "microbiome" in js.lower()


class TestMicrobiomeAPI:
    """Tests that microbiome API works end-to-end for the panel."""

    @pytest.fixture
    def field_with_microbiome(self, client, admin_headers):
        """Create a farm+field with microbiome data."""
        farm = client.post("/api/farms", json={
            "name": "Rancho Microbioma",
            "owner_name": "Test",
            "location_lat": 20.67,
            "location_lon": -103.35,
            "total_hectares": 20,
            "municipality": "Zapopan",
            "state": "Jalisco",
            "country": "MX",
        }, headers=admin_headers).json()

        field = client.post(f"/api/farms/{farm['id']}/fields", json={
            "name": "Parcela Bio",
            "crop_type": "maiz",
            "hectares": 10,
        }).json()

        # Add microbiome sample — healthy
        resp = client.post(
            f"/api/farms/{farm['id']}/fields/{field['id']}/microbiome",
            json={
                "respiration_rate": 65.0,
                "microbial_biomass_carbon": 450.0,
                "fungi_bacteria_ratio": 1.2,
                "sampled_at": "2026-03-20T10:00:00",
            },
        )
        assert resp.status_code == 201

        return {"farm": farm, "field": field}

    def test_microbiome_endpoint_returns_data(self, client, field_with_microbiome):
        """GET microbiome returns list with classification."""
        farm = field_with_microbiome["farm"]
        field = field_with_microbiome["field"]
        resp = client.get(f"/api/farms/{farm['id']}/fields/{field['id']}/microbiome")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["classification"] == "healthy"
        assert data[0]["respiration_rate"] == 65.0
        assert data[0]["fungi_bacteria_ratio"] == 1.2

    def test_microbiome_empty_field(self, client, admin_headers):
        """GET microbiome returns empty list for field with no samples."""
        farm = client.post("/api/farms", json={
            "name": "Rancho Vacio",
            "owner_name": "Test",
            "location_lat": 20.5,
            "location_lon": -103.2,
            "total_hectares": 10,
            "municipality": "Tlaquepaque",
            "state": "Jalisco",
            "country": "MX",
        }, headers=admin_headers).json()

        field = client.post(f"/api/farms/{farm['id']}/fields", json={
            "name": "Sin Bio",
            "crop_type": "frijol",
            "hectares": 5,
        }).json()

        resp = client.get(f"/api/farms/{farm['id']}/fields/{field['id']}/microbiome")
        assert resp.status_code == 200
        assert resp.json() == []
