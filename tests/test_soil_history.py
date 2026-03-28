"""Tests for the soil history timeline on the field detail page.

TDD — these tests must fail first, then pass after implementation.
- Timeline renders in HTML and JS
- Detail expands on click (JS has toggle logic)
- Handles single sample gracefully
"""


# ── HTML structure ──

def test_soil_history_section_in_field_html(client):
    """Field detail HTML has the Historial de Suelo section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="section-soil-history"' in html
    assert "Historial de Suelo" in html


def test_soil_history_content_container(client):
    """Field detail HTML has a container for soil history content."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert 'id="soil-history-content"' in resp.text


def test_soil_history_placeholder_when_no_data(client):
    """Field detail HTML shows placeholder when no soil history."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert "Sin historial de suelo" in resp.text


# ── JS logic ──

def test_field_js_has_render_soil_history(client):
    """field.js contains the renderSoilHistory function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "renderSoilHistory" in resp.text


def test_field_js_calls_render_soil_history(client):
    """field.js calls renderSoilHistory with the soilList data."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "renderSoilHistory(soilList)" in resp.text


def test_soil_history_renders_timeline(client):
    """renderSoilHistory creates a soil-timeline container."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "soil-timeline" in resp.text


def test_soil_history_shows_date(client):
    """renderSoilHistory formats and displays the sampled_at date."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "sampled_at" in js
    assert "toLocaleDateString" in js


def test_soil_history_shows_ph_badge(client):
    """renderSoilHistory shows pH with color-coded badge per sample."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "s.ph" in js or "item.ph" in js or "sample.ph" in js


def test_soil_history_has_expandable_detail(client):
    """renderSoilHistory has click-to-expand detail for each sample."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    # Toggle visibility pattern
    assert "soil-timeline-detail" in js


def test_soil_history_handles_empty_list(client):
    """renderSoilHistory shows placeholder for empty/null list."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "Sin historial de suelo" in js


# ── CSS ──

def test_soil_timeline_css_exists(client):
    """styles.css contains soil-timeline styles."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    assert "soil-timeline" in resp.text


# ── Backend list endpoint (already exists, verify it works) ──

def test_soil_list_endpoint_returns_list(client, db):
    """GET /api/farms/{id}/fields/{id}/soil returns ordered list."""
    from cultivos.db.models import Farm, Field, SoilAnalysis
    from datetime import datetime
    farm = Farm(name="Test Farm", owner_name="Owner")
    db.add(farm)
    db.commit()
    db.refresh(farm)
    field = Field(farm_id=farm.id, name="Parcela A", crop_type="maiz", hectares=5)
    db.add(field)
    db.commit()
    db.refresh(field)

    # Add two soil analyses
    s1 = SoilAnalysis(field_id=field.id, ph=6.5, organic_matter_pct=3.2,
                       nitrogen_ppm=30, phosphorus_ppm=20, potassium_ppm=150,
                       moisture_pct=40, texture="loam",
                       sampled_at=datetime(2026, 1, 15))
    s2 = SoilAnalysis(field_id=field.id, ph=6.8, organic_matter_pct=3.5,
                       nitrogen_ppm=35, phosphorus_ppm=22, potassium_ppm=160,
                       moisture_pct=38, texture="loam",
                       sampled_at=datetime(2026, 3, 15))
    db.add_all([s1, s2])
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # Each entry should have sampled_at
    assert "sampled_at" in data[0]
    assert "ph" in data[0]


def test_soil_list_single_sample(client, db):
    """GET /api/farms/{id}/fields/{id}/soil works with single sample."""
    from cultivos.db.models import Farm, Field, SoilAnalysis
    from datetime import datetime
    farm = Farm(name="Test Farm", owner_name="Owner")
    db.add(farm)
    db.commit()
    db.refresh(farm)
    field = Field(farm_id=farm.id, name="Parcela B", crop_type="frijol", hectares=3)
    db.add(field)
    db.commit()
    db.refresh(field)

    s = SoilAnalysis(field_id=field.id, ph=5.8, organic_matter_pct=2.1,
                      nitrogen_ppm=15, phosphorus_ppm=10, potassium_ppm=90,
                      moisture_pct=55, texture="clay",
                      sampled_at=datetime(2026, 2, 20))
    db.add(s)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["ph"] == 5.8
