"""Tests for the treatment effectiveness detail card on the field detail page."""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import Farm, Field, HealthScore, SoilAnalysis


@pytest.fixture
def seeded_farm(db, client, admin_headers):
    """Create farm, field, health scores, and an applied treatment for effectiveness testing."""
    farm = Farm(name="Rancho Efectividad", owner_name="Owner")
    db.add(farm)
    db.commit()
    db.refresh(farm)

    field = Field(farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=10)
    db.add(field)
    db.commit()
    db.refresh(field)

    # Health score BEFORE treatment (low)
    now = datetime.utcnow()
    hs_before = HealthScore(
        field_id=field.id, score=35.0, trend="declining",
        sources=["ndvi"], breakdown={"ndvi": 35.0},
        scored_at=now - timedelta(days=10),
    )
    # Health score AFTER treatment (improved)
    hs_after = HealthScore(
        field_id=field.id, score=72.0, trend="improving",
        sources=["ndvi"], breakdown={"ndvi": 72.0},
        scored_at=now - timedelta(days=2),
    )
    db.add_all([hs_before, hs_after])

    # Soil data to trigger treatment generation
    soil = SoilAnalysis(
        field_id=field.id, ph=8.5, organic_matter_pct=1.0,
        nitrogen_ppm=10, phosphorus_ppm=8, potassium_ppm=50,
        moisture_pct=15, sampled_at=now - timedelta(days=15),
    )
    db.add(soil)
    db.commit()

    # Generate treatments via API, then mark one as applied
    resp = client.post(f"/api/farms/{farm.id}/fields/{field.id}/treatments")
    assert resp.status_code == 201, f"Treatment generation failed: {resp.text}"
    treatments = resp.json()
    assert len(treatments) > 0

    tid = treatments[0]["id"]
    applied_at = (now - timedelta(days=5)).isoformat()
    resp = client.post(
        f"/api/farms/{farm.id}/fields/{field.id}/treatments/{tid}/applied",
        json={"applied_at": applied_at, "notes": "Aplicado manualmente"},
    )
    assert resp.status_code == 200

    return {"farm_id": farm.id, "field_id": field.id, "treatment_id": tid}


# ── HTML structure tests ──


def test_effectiveness_section_in_html(client):
    """Field detail HTML has the treatment effectiveness section container."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    text = resp.text
    assert 'id="section-treatment-effectiveness"' in text
    assert "Efectividad de Tratamientos" in text


def test_effectiveness_placeholder(client):
    """Effectiveness section shows a placeholder when empty."""
    resp = client.get("/campo")
    text = resp.text
    assert 'id="treatment-effectiveness-content"' in text
    assert "Sin datos de efectividad" in text


# ── API response tests ──


def test_effectiveness_endpoint_returns_data(client, seeded_farm):
    """GET effectiveness for an applied treatment returns before/after scores."""
    fid = seeded_farm["farm_id"]
    flid = seeded_farm["field_id"]
    tid = seeded_farm["treatment_id"]
    resp = client.get(f"/api/farms/{fid}/fields/{flid}/treatments/{tid}/effectiveness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["treatment_id"] == tid
    assert data["score_before"] is not None
    assert data["score_after"] is not None
    assert data["delta"] is not None
    assert data["status"] in ("effective", "ineffective", "neutral", "insufficient_data", "not_applied")


def test_effectiveness_delta_positive_for_improvement(client, seeded_farm):
    """When health improved after treatment, delta is positive and status is effective."""
    fid = seeded_farm["farm_id"]
    flid = seeded_farm["field_id"]
    tid = seeded_farm["treatment_id"]
    resp = client.get(f"/api/farms/{fid}/fields/{flid}/treatments/{tid}/effectiveness")
    data = resp.json()
    # Score went from 35 to 72 = +37
    assert data["delta"] > 0
    assert data["status"] == "effective"


def test_effectiveness_not_applied_treatment(client, db):
    """Unapplied treatment returns status not_applied with null scores."""
    farm = Farm(name="Rancho Sin Aplicar", owner_name="Owner")
    db.add(farm)
    db.commit()
    db.refresh(farm)
    field = Field(farm_id=farm.id, name="Campo B", crop_type="maiz", hectares=5)
    db.add(field)
    db.commit()
    db.refresh(field)
    hs = HealthScore(
        field_id=field.id, score=30, trend="declining",
        sources=["ndvi"], breakdown={"ndvi": 30.0},
    )
    soil = SoilAnalysis(
        field_id=field.id, ph=8.5, organic_matter_pct=1.0,
        nitrogen_ppm=10, phosphorus_ppm=8, potassium_ppm=50,
        moisture_pct=15, sampled_at=datetime.utcnow(),
    )
    db.add_all([hs, soil])
    db.commit()
    # Generate but don't apply
    resp = client.post(f"/api/farms/{farm.id}/fields/{field.id}/treatments")
    assert resp.status_code == 201
    tid = resp.json()[0]["id"]
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/treatments/{tid}/effectiveness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "not_applied"
    assert data["score_before"] is None
    assert data["score_after"] is None
    assert data["delta"] is None


# ── JS rendering tests ──


def test_field_js_has_effectiveness_function(client):
    """field.js contains the renderTreatmentEffectiveness function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    text = resp.text
    assert "renderTreatmentEffectiveness" in text


def test_field_js_fetches_effectiveness(client):
    """field.js fetches the effectiveness endpoint for applied treatments."""
    resp = client.get("/field.js")
    text = resp.text
    assert "/effectiveness" in text


def test_effectiveness_card_shows_delta_label(client):
    """field.js renders delta with a sign indicator."""
    resp = client.get("/field.js")
    text = resp.text
    # Should show delta with + or - prefix
    assert "delta" in text.lower()


def test_effectiveness_card_shows_status_badge(client):
    """field.js renders status badge with Spanish labels."""
    resp = client.get("/field.js")
    text = resp.text
    assert "Efectivo" in text or "efectivo" in text
    assert "Sin efecto" in text or "sin efecto" in text


# ── CSS tests ──


def test_effectiveness_styles_exist(client):
    """styles.css has treatment effectiveness card styles."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    text = resp.text
    assert "treatment-effectiveness" in text
