"""Tests for the Cerebro intelligence summary card on the field detail page."""

import pytest


@pytest.fixture
def farm_with_full_data(client, admin_headers):
    """Create a farm with a field that has all Cerebro data sources."""
    farm = client.post("/api/farms", json={
        "name": "Rancho Cerebro",
        "owner_name": "Test Owner",
        "location_lat": 20.67,
        "location_lon": -103.35,
        "total_hectares": 30,
        "municipality": "Zapopan",
        "state": "Jalisco",
        "country": "MX",
    }, headers=admin_headers).json()

    field = client.post(f"/api/farms/{farm['id']}/fields", json={
        "name": "Parcela Cerebro",
        "crop_type": "maiz",
        "hectares": 15,
    }).json()

    # Soil
    client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/soil", json={
        "ph": 6.5,
        "organic_matter_pct": 3.0,
        "nitrogen_ppm": 40,
        "phosphorus_ppm": 25,
        "potassium_ppm": 200,
        "texture": "franco",
        "moisture_pct": 30,
        "sampled_at": "2026-03-20T10:00:00",
    })

    # NDVI
    client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/ndvi", json={
        "nir_band": [[0.5, 0.6, 0.55], [0.58, 0.62, 0.57], [0.54, 0.59, 0.56]],
        "red_band": [[0.1, 0.08, 0.09], [0.07, 0.06, 0.08], [0.1, 0.07, 0.09]],
    })

    # Thermal
    client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/thermal", json={
        "thermal_band": [[32.0, 33.0, 31.5], [34.0, 36.0, 33.0], [31.0, 32.5, 34.5]],
    })

    # Health score
    client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/health")

    return {"farm": farm, "field": field}


# ── HTML structure tests ──

def test_cerebro_section_present_in_html(client):
    """Field detail HTML has the Resumen Cerebro section container."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="section-cerebro"' in html
    assert "Resumen Cerebro" in html


def test_cerebro_subsections_present(client):
    """Cerebro card has containers for all intelligence subsections."""
    resp = client.get("/campo")
    html = resp.text
    assert 'id="cerebro-content"' in html


# ── Intelligence API integration ──

def test_intelligence_endpoint_returns_data(client, farm_with_full_data):
    """GET /intelligence returns all Cerebro sections for a field with data."""
    farm = farm_with_full_data["farm"]
    field = farm_with_full_data["field"]
    resp = client.get(
        f"/api/farms/{farm['id']}/fields/{field['id']}/intelligence"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["field_id"] == field["id"]
    assert data["health"] is not None
    assert data["ndvi"] is not None
    assert data["soil"] is not None


def test_intelligence_handles_empty_field(client, admin_headers):
    """GET /intelligence returns null sections for a field with no data."""
    farm = client.post("/api/farms", json={
        "name": "Rancho Vacio",
        "owner_name": "Test",
        "location_lat": 20.5,
        "location_lon": -103.2,
        "total_hectares": 10,
        "municipality": "Zapopan",
        "state": "Jalisco",
        "country": "MX",
    }, headers=admin_headers).json()

    field = client.post(f"/api/farms/{farm['id']}/fields", json={
        "name": "Campo Vacio",
        "crop_type": "frijol",
        "hectares": 5,
    }).json()

    resp = client.get(
        f"/api/farms/{farm['id']}/fields/{field['id']}/intelligence"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["health"] is None
    assert data["ndvi"] is None
    assert data["thermal"] is None
    assert data["soil"] is None


# ── Enhanced Cerebro card: top risk, next action, yield, confidence ──

def test_intelligence_yields_present(client, farm_with_full_data):
    """Intelligence endpoint includes yield prediction data when available."""
    farm = farm_with_full_data["farm"]
    field = farm_with_full_data["field"]
    resp = client.get(
        f"/api/farms/{farm['id']}/fields/{field['id']}/intelligence"
    )
    data = resp.json()
    # yield_prediction may be None if no planted_at, but key must exist
    assert "yield_prediction" in data


def test_intelligence_fusion_present(client, farm_with_full_data):
    """Intelligence endpoint includes fusion/confidence data."""
    farm = farm_with_full_data["farm"]
    field = farm_with_full_data["field"]
    resp = client.get(
        f"/api/farms/{farm['id']}/fields/{field['id']}/intelligence"
    )
    data = resp.json()
    assert "fusion" in data


def test_intelligence_disease_risk_present(client, farm_with_full_data):
    """Intelligence endpoint includes disease risk for top-risk derivation."""
    farm = farm_with_full_data["farm"]
    field = farm_with_full_data["field"]
    resp = client.get(
        f"/api/farms/{farm['id']}/fields/{field['id']}/intelligence"
    )
    data = resp.json()
    assert "disease_risk" in data


def test_intelligence_treatments_present(client, farm_with_full_data):
    """Intelligence endpoint includes treatments for next-action derivation."""
    farm = farm_with_full_data["farm"]
    field = farm_with_full_data["field"]
    resp = client.get(
        f"/api/farms/{farm['id']}/fields/{field['id']}/intelligence"
    )
    data = resp.json()
    assert "treatments" in data
    assert isinstance(data["treatments"], list)


# ── Frontend JS tests ──

def test_field_js_has_cerebro_render(client):
    """field.js contains the renderCerebro function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "renderCerebro" in js


def test_field_js_fetches_intelligence(client):
    """field.js fetches the /intelligence endpoint."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "/intelligence" in js


def test_cerebro_renders_yield_estimate(client):
    """Cerebro card JS renders yield estimate section."""
    resp = client.get("/field.js")
    js = resp.text
    assert "yield_prediction" in js or "yield" in js
    assert "kg/ha" in js


def test_cerebro_renders_sensor_confidence(client):
    """Cerebro card JS renders sensor confidence from fusion data."""
    resp = client.get("/field.js")
    js = resp.text
    assert "fusion" in js or "confidence" in js
    assert "Confianza" in js


def test_cerebro_renders_top_risk(client):
    """Cerebro card JS renders top risk indicator."""
    resp = client.get("/field.js")
    js = resp.text
    assert "cerebro-risk" in js or "Riesgo Principal" in js


def test_cerebro_renders_next_action(client):
    """Cerebro card JS renders next recommended action."""
    resp = client.get("/field.js")
    js = resp.text
    assert "cerebro-action" in js or "Accion" in js


def test_cerebro_handles_partial_data(client):
    """Cerebro card shows placeholders when data is missing."""
    resp = client.get("/field.js")
    js = resp.text
    assert "Sin datos" in js or "campo-placeholder" in js


# ── CSS tests ──

def test_cerebro_styles_present(client):
    """styles.css has the cerebro card styling."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    css = resp.text
    assert "cerebro" in css.lower()


def test_cerebro_enhanced_styles(client):
    """styles.css has styles for the enhanced Cerebro sections."""
    resp = client.get("/styles.css")
    css = resp.text
    assert "cerebro-insights" in css
    assert "cerebro-insight-item" in css
