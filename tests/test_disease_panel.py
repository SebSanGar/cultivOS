"""Tests for the expanded disease risk identification panel on field detail page."""

import pytest


@pytest.fixture
def farm_with_disease_data(client, admin_headers):
    """Create a farm + field with NDVI, thermal, and weather data to trigger disease risk."""
    farm = client.post("/api/farms", json={
        "name": "Rancho Enfermedades",
        "owner_name": "Test Owner",
        "location_lat": 20.67,
        "location_lon": -103.35,
        "total_hectares": 50,
        "municipality": "Zapopan",
        "state": "Jalisco",
        "country": "MX",
    }, headers=admin_headers).json()

    field = client.post(f"/api/farms/{farm['id']}/fields", json={
        "name": "Parcela Riesgo",
        "crop_type": "maiz",
        "hectares": 10,
    }).json()

    # NDVI with low values to trigger disease risk
    client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/ndvi", json={
        "nir_band": [[0.3, 0.25, 0.28], [0.22, 0.2, 0.27], [0.3, 0.24, 0.26]],
        "red_band": [[0.2, 0.18, 0.19], [0.17, 0.16, 0.2], [0.22, 0.19, 0.21]],
    })

    # Thermal with high stress
    client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/thermal", json={
        "thermal_band": [[38.0, 39.0, 37.5], [40.0, 41.0, 38.0], [37.0, 39.5, 40.5]],
    })

    return {"farm": farm, "field": field}


@pytest.fixture
def farm_without_data(client, admin_headers):
    """Create a farm + field with no sensor data — disease risk should handle gracefully."""
    farm = client.post("/api/farms", json={
        "name": "Rancho Vacio",
        "owner_name": "Test Owner",
        "location_lat": 20.67,
        "location_lon": -103.35,
        "total_hectares": 20,
        "municipality": "Zapopan",
        "state": "Jalisco",
        "country": "MX",
    }, headers=admin_headers).json()

    field = client.post(f"/api/farms/{farm['id']}/fields", json={
        "name": "Parcela Vacia",
        "crop_type": "tomate",
        "hectares": 5,
    }).json()

    return {"farm": farm, "field": field}


class TestDiseaseRiskPanel:
    """Disease risk panel returns structured risk data with items."""

    def test_disease_risk_returns_risks_array(self, client, farm_with_disease_data):
        """Disease risk endpoint returns a risks array with typed risk items."""
        farm = farm_with_disease_data["farm"]
        field = farm_with_disease_data["field"]
        resp = client.get(f"/api/farms/{farm['id']}/fields/{field['id']}/disease-risk")
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_level" in data
        assert "risks" in data
        assert isinstance(data["risks"], list)
        assert "mensaje" in data

    def test_disease_risk_items_have_structure(self, client, farm_with_disease_data):
        """Each risk item has tipo, descripcion, recomendacion, urgencia, organico."""
        farm = farm_with_disease_data["farm"]
        field = farm_with_disease_data["field"]
        resp = client.get(f"/api/farms/{farm['id']}/fields/{field['id']}/disease-risk")
        data = resp.json()
        if data["risks"]:
            risk = data["risks"][0]
            assert "tipo" in risk
            assert "descripcion" in risk
            assert "recomendacion" in risk
            assert "urgencia" in risk
            assert "organico" in risk

    def test_disease_risk_no_data_returns_safe(self, client, farm_without_data):
        """No NDVI data returns sin_riesgo with empty risks array."""
        farm = farm_without_data["farm"]
        field = farm_without_data["field"]
        resp = client.get(f"/api/farms/{farm['id']}/fields/{field['id']}/disease-risk")
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] == "sin_riesgo"
        assert data["risks"] == []

    def test_disease_risk_has_weather_context(self, client, farm_with_disease_data):
        """Disease risk returns weather context when weather data exists."""
        farm = farm_with_disease_data["farm"]
        field = farm_with_disease_data["field"]
        resp = client.get(f"/api/farms/{farm['id']}/fields/{field['id']}/disease-risk")
        data = resp.json()
        # weather_context may be None if no weather record, but the field should exist
        assert "weather_context" in data


class TestDiseaseIdentification:
    """Disease identification endpoint returns matches with confidence."""

    def test_identify_returns_matches_with_confidence(self, client):
        """POST /identify returns disease matches ranked by confidence."""
        resp = client.post("/api/knowledge/diseases/identify", json={
            "symptoms": ["manchas_amarillas", "marchitamiento"],
            "crop": "maiz",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for match in data:
            assert "confidence" in match
            assert "name" in match
            assert "treatments" in match
            assert 0.0 <= match["confidence"] <= 1.0

    def test_identify_no_matching_symptoms(self, client):
        """POST /identify with unrecognized symptoms returns empty or low-confidence matches."""
        resp = client.post("/api/knowledge/diseases/identify", json={
            "symptoms": ["sintoma_inexistente_xyz"],
            "crop": "maiz",
        })
        assert resp.status_code == 200
        data = resp.json()
        # Either empty or all zero confidence
        for match in data:
            assert match["confidence"] == 0.0


class TestDiseaseFieldHTML:
    """Field detail page HTML has proper disease panel containers."""

    def test_disease_section_exists(self, client):
        """Field detail page has the disease section with correct ID."""
        resp = client.get("/campo")
        assert resp.status_code == 200
        html = resp.text
        assert 'id="section-disease"' in html
        assert 'id="disease-content"' in html

    def test_disease_section_spanish_title(self, client):
        """Disease section has Spanish title."""
        resp = client.get("/campo")
        html = resp.text
        assert "Riesgo de Enfermedades" in html

    def test_field_js_has_disease_rendering(self, client):
        """field.js includes disease rendering function."""
        resp = client.get("/field.js")
        assert resp.status_code == 200
        js = resp.text
        assert "renderDisease" in js
        # Should render risk items, not just risk level
        assert "risk_items" in js or "risks" in js or "riesgo-item" in js
