"""Tests for the multi-field comparison table on the farm dashboard."""

import pytest
from cultivos.db.models import Farm, Field, HealthScore, SoilAnalysis, TreatmentRecord, NDVIResult
from datetime import datetime


@pytest.fixture
def farm_with_multiple_fields(db):
    """Create a farm with 3 fields having varied data."""
    farm = Farm(name="Rancho Comparativo", state="Jalisco", total_hectares=75)
    db.add(farm)
    db.flush()

    f1 = Field(farm_id=farm.id, name="Parcela Maiz", crop_type="maiz", hectares=25)
    f2 = Field(farm_id=farm.id, name="Parcela Agave", crop_type="agave", hectares=30)
    f3 = Field(farm_id=farm.id, name="Parcela Frijol", crop_type="frijol", hectares=20)
    db.add_all([f1, f2, f3])
    db.flush()

    # Field 1: full data
    db.add(HealthScore(field_id=f1.id, score=85.0, trend="improving", scored_at=datetime(2026, 3, 1)))
    db.add(NDVIResult(field_id=f1.id, ndvi_mean=0.72, ndvi_std=0.1, ndvi_min=0.5, ndvi_max=0.9, pixels_total=1000, stress_pct=5.0, zones=[], analyzed_at=datetime(2026, 3, 1)))
    db.add(SoilAnalysis(field_id=f1.id, ph=6.5, organic_matter_pct=3.2, nitrogen_ppm=45, phosphorus_ppm=30, potassium_ppm=200, texture="franco", moisture_pct=28, sampled_at=datetime(2026, 3, 1)))
    db.add(TreatmentRecord(field_id=f1.id, health_score_used=70, problema="Baja N", causa_probable="suelo", tratamiento="Composta", urgencia="media", prevencion="rotacion", organic=True, costo_estimado_mxn=500))

    # Field 2: partial data (health + NDVI only)
    db.add(HealthScore(field_id=f2.id, score=55.0, trend="declining", scored_at=datetime(2026, 3, 1)))
    db.add(NDVIResult(field_id=f2.id, ndvi_mean=0.45, ndvi_std=0.08, ndvi_min=0.3, ndvi_max=0.6, pixels_total=800, stress_pct=15.0, zones=[], analyzed_at=datetime(2026, 3, 1)))

    # Field 3: no data at all

    db.commit()
    return {"farm_id": farm.id, "field_ids": [f1.id, f2.id, f3.id]}


@pytest.fixture
def single_field_farm(db):
    """Create a farm with just one field."""
    farm = Farm(name="Rancho Pequeno", state="Jalisco", total_hectares=10)
    db.add(farm)
    db.flush()
    f1 = Field(farm_id=farm.id, name="Unico Campo", crop_type="maiz", hectares=10)
    db.add(f1)
    db.flush()
    db.add(HealthScore(field_id=f1.id, score=60.0, trend="stable", scored_at=datetime(2026, 3, 1)))
    db.commit()
    return {"farm_id": farm.id}


# -- API (data-completeness provides per-field breakdown) --

def test_data_completeness_returns_per_field(client, farm_with_multiple_fields):
    """GET /data-completeness returns per-field breakdown for comparison table."""
    fid = farm_with_multiple_fields["farm_id"]
    resp = client.get(f"/api/farms/{fid}/data-completeness")
    assert resp.status_code == 200
    data = resp.json()
    assert "fields" in data
    assert len(data["fields"]) == 3
    for field in data["fields"]:
        assert "field_id" in field
        assert "score" in field


def test_heatmap_returns_health_scores(client, farm_with_multiple_fields):
    """GET /heatmap returns per-field health scores for comparison table."""
    fid = farm_with_multiple_fields["farm_id"]
    resp = client.get(f"/api/farms/{fid}/heatmap")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["fields"]) == 3
    scores = [f["health_score"] for f in data["fields"]]
    assert 85.0 in scores
    assert 55.0 in scores


# -- HTML structure --

def test_comparison_table_container_in_dashboard(client):
    """Dashboard HTML has the comparison-table container."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="field-comparison-panel"' in html


def test_comparison_table_hidden_by_default(client):
    """Comparison table container is hidden by default."""
    resp = client.get("/")
    html = resp.text
    idx = html.index('id="field-comparison-panel"')
    tag_start = html.rfind('<div', 0, idx)
    tag_end = html.index('>', idx)
    tag_snippet = html[tag_start:tag_end + 1]
    assert 'display:none' in tag_snippet


# -- Frontend JS --

def test_app_js_has_comparison_render_function(client):
    """app.js contains renderFieldComparison function."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "renderFieldComparison" in js


def test_app_js_fetches_data_completeness(client):
    """app.js fetches the /data-completeness endpoint for comparison data."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "data-completeness" in js


def test_app_js_has_sort_logic(client):
    """app.js contains sorting logic for the comparison table."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "sortField" in js or "sortComparison" in js or "sort(" in js


# -- CSS --

def test_comparison_table_styles_present(client):
    """styles.css has comparison table styling."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    css = resp.text
    assert "comparison" in css.lower()
