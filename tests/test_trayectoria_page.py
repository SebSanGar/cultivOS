"""Tests for the health trajectory page at /trayectoria."""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord


def _seed_trajectory_data(db):
    """Seed farm with field, health scores over time, and treatments."""
    farm = Farm(name="Rancho Trayectoria", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Norte", hectares=10.0, crop_type="maiz")
    db.add(field)
    db.flush()

    now = datetime.utcnow()
    # Create health scores over 4 weeks (improving trend)
    for i, score_val in enumerate([55.0, 60.0, 68.0, 75.0]):
        hs = HealthScore(
            field_id=field.id,
            score=score_val,
            ndvi_mean=0.5 + i * 0.05,
            sources=["ndvi"],
            breakdown={},
            scored_at=now - timedelta(days=28 - i * 7),
        )
        db.add(hs)

    # Add a treatment between 2nd and 3rd score
    tr = TreatmentRecord(
        field_id=field.id,
        health_score_used=60.0,
        tratamiento="Composta organica",
        problema="Baja materia organica",
        causa_probable="Suelo agotado",
        urgencia="media",
        prevencion="Aplicar cada 3 meses",
        applied_at=now - timedelta(days=17),
    )
    db.add(tr)
    db.commit()
    return farm, field


# ── Page Load Tests ────────────────────────────────────────────


class TestTrayectoriaPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/trayectoria")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/trayectoria")
        assert "Trayectoria de Salud" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/trayectoria")
        assert 'id="traj-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/trayectoria")
        assert 'id="traj-field-select"' in resp.text

    def test_page_has_trajectory_chart_container(self, client):
        resp = client.get("/trayectoria")
        assert 'id="traj-chart"' in resp.text

    def test_page_has_treatment_links_container(self, client):
        resp = client.get("/trayectoria")
        assert 'id="traj-treatments"' in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/trayectoria")
        assert 'id="traj-empty"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/trayectoria")
        html = resp.text
        assert 'id="traj-stat-current"' in html
        assert 'id="traj-stat-trend"' in html
        assert 'id="traj-stat-projection"' in html

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/trayectoria")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/trayectoria")
        assert "trayectoria.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/trayectoria")
        assert "intel-nav" in resp.text

    def test_page_has_projection_card(self, client):
        resp = client.get("/trayectoria")
        assert 'id="traj-projection"' in resp.text

    def test_page_has_score_range_section(self, client):
        resp = client.get("/trayectoria")
        assert 'id="traj-range"' in resp.text


# ── API Integration Tests ──────────────────────────────────────


class TestTrajectoryAPI:
    """Trajectory API returns expected data."""

    def test_trajectory_returns_data(self, client, db):
        farm, field = _seed_trajectory_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health/trajectory")
        assert resp.status_code == 200
        data = resp.json()
        assert "trend" in data
        assert "rate_of_change" in data
        assert "projection" in data
        assert "current_score" in data
        assert "score_range" in data
        assert "treatment_links" in data

    def test_trajectory_trend_is_improving(self, client, db):
        farm, field = _seed_trajectory_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health/trajectory")
        data = resp.json()
        assert data["trend"] == "improving"
        assert data["rate_of_change"] > 0

    def test_trajectory_has_treatment_correlations(self, client, db):
        farm, field = _seed_trajectory_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health/trajectory")
        data = resp.json()
        assert len(data["treatment_links"]) >= 1
        link = data["treatment_links"][0]
        assert "tratamiento" in link
        assert "delta" in link
        assert "health_before" in link
        assert "health_after" in link

    def test_trajectory_current_score(self, client, db):
        farm, field = _seed_trajectory_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health/trajectory")
        data = resp.json()
        assert data["current_score"] == 75.0

    def test_trajectory_score_range(self, client, db):
        farm, field = _seed_trajectory_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health/trajectory")
        data = resp.json()
        assert data["score_range"]["min"] == 55.0
        assert data["score_range"]["max"] == 75.0

    def test_404_for_missing_farm(self, client, db):
        resp = client.get("/api/farms/9999/fields/1/health/trajectory")
        assert resp.status_code == 404

    def test_404_for_missing_field(self, client, db):
        farm = Farm(name="Solo", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/9999/health/trajectory")
        assert resp.status_code == 404

    def test_trajectory_with_no_data(self, client, db):
        """Field with no health scores returns gracefully."""
        farm = Farm(name="Vacia", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Sin Datos", hectares=5.0, crop_type="frijol")
        db.add(field)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health/trajectory")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data_points"] == 0
        assert data["treatment_links"] == []


# ── Page Content Tests ─────────────────────────────────────────


class TestTrayectoriaPageContent:
    """Page HTML has correct structure for trajectory rendering."""

    def test_page_has_trayectoria_link_in_nav(self, client):
        resp = client.get("/trayectoria")
        assert "/trayectoria" in resp.text

    def test_page_has_treatment_correlation_label(self, client):
        resp = client.get("/trayectoria")
        html = resp.text
        assert "Tratamientos" in html or "Correlacion" in html

    def test_page_has_trend_label(self, client):
        resp = client.get("/trayectoria")
        assert "Tendencia" in resp.text

    def test_page_has_footer(self, client):
        resp = client.get("/trayectoria")
        assert "cultivos-footer" in resp.text
