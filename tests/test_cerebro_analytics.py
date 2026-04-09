"""Tests for Cerebro AI decision log + analytics at /cerebro-analytics."""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import (
    Alert,
    Farm,
    FarmerFeedback,
    Field,
    HealthScore,
    NDVIResult,
    ThermalResult,
    TreatmentRecord,
)


def _seed_cerebro_data(db):
    """Seed diverse AI decision data across multiple tables."""
    farm = Farm(name="Rancho Cerebro", state="Jalisco", total_hectares=80.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela IA", hectares=20.0, crop_type="maiz")
    db.add(field)
    db.flush()

    now = datetime.utcnow()

    # Health scores (AI assessments)
    for i in range(5):
        db.add(HealthScore(
            field_id=field.id, score=60.0 + i * 5, ndvi_mean=0.5,
            sources=["ndvi"], breakdown={},
            scored_at=now - timedelta(days=30 - i * 7),
        ))

    # Treatment records (AI recommendations)
    for i in range(3):
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=65.0,
            tratamiento=f"Tratamiento {i+1}", problema="Baja salud",
            causa_probable="Suelo", urgencia="media", prevencion="Monitorear",
            created_at=now - timedelta(days=20 - i * 5),
        ))

    # NDVI analyses
    for i in range(4):
        db.add(NDVIResult(
            field_id=field.id, ndvi_mean=0.55, ndvi_std=0.1,
            ndvi_min=0.3, ndvi_max=0.8, pixels_total=1000,
            stress_pct=15.0, zones=[],
            analyzed_at=now - timedelta(days=28 - i * 7),
        ))

    # Thermal analyses
    for i in range(2):
        db.add(ThermalResult(
            field_id=field.id, temp_mean=28.0, temp_std=3.0,
            temp_min=22.0, temp_max=35.0, pixels_total=1000,
            stress_pct=10.0,
            analyzed_at=now - timedelta(days=14 - i * 7),
        ))

    db.flush()

    # Alerts
    for i in range(3):
        db.add(Alert(
            farm_id=farm.id, field_id=field.id,
            alert_type="low_health", message=f"Alerta {i+1}",
            status="sent",
            created_at=now - timedelta(days=10 - i * 3),
        ))

    db.flush()

    # Farmer feedback
    tr = db.query(TreatmentRecord).first()
    db.add(FarmerFeedback(
        field_id=field.id, treatment_id=tr.id,
        rating=4, worked=True, farmer_notes="Funciono bien",
    ))

    db.commit()
    return farm, field


# ── Page Load Tests ────────────────────────────────────────────


class TestCerebroAnalyticsPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/cerebro-analytics")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/cerebro-analytics")
        assert "Cerebro Analytics" in resp.text or "Cerebro IA" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/cerebro-analytics")
        html = resp.text
        assert 'id="cerebro-stat-total"' in html
        assert 'id="cerebro-stat-recommendations"' in html
        assert 'id="cerebro-stat-analyses"' in html

    def test_page_has_chart_container(self, client):
        resp = client.get("/cerebro-analytics")
        assert 'id="cerebro-chart"' in resp.text

    def test_page_has_decisions_table(self, client):
        resp = client.get("/cerebro-analytics")
        assert 'id="cerebro-decisions"' in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/cerebro-analytics")
        assert "intel-nav" in resp.text

    def test_page_has_js_script(self, client):
        resp = client.get("/cerebro-analytics")
        assert "cerebro-analytics.js" in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/cerebro-analytics")
        html = resp.text
        assert "Decisiones" in html or "decisiones" in html

    def test_page_has_footer(self, client):
        resp = client.get("/cerebro-analytics")
        assert "cultivos-footer" in resp.text

    def test_page_has_accuracy_section(self, client):
        resp = client.get("/cerebro-analytics")
        assert 'id="cerebro-accuracy"' in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/cerebro-analytics")
        assert 'id="cerebro-empty"' in resp.text


# ── API Tests ─────────────────────────────────────────────────


class TestCerebroAnalyticsAPI:
    """API returns expected analytics data."""

    def test_endpoint_returns_200(self, client, db):
        _seed_cerebro_data(db)
        resp = client.get("/api/intel/cerebro-analytics")
        assert resp.status_code == 200

    def test_returns_total_decisions(self, client, db):
        _seed_cerebro_data(db)
        resp = client.get("/api/intel/cerebro-analytics")
        data = resp.json()
        assert "total_decisions" in data
        # 5 health + 3 treatments + 4 NDVI + 2 thermal + 3 alerts = 17
        assert data["total_decisions"] == 17

    def test_returns_decisions_by_type(self, client, db):
        _seed_cerebro_data(db)
        resp = client.get("/api/intel/cerebro-analytics")
        data = resp.json()
        by_type = data["decisions_by_type"]
        assert by_type["health_assessments"] == 5
        assert by_type["treatment_recommendations"] == 3
        assert by_type["ndvi_analyses"] == 4
        assert by_type["thermal_analyses"] == 2
        assert by_type["alerts_generated"] == 3

    def test_returns_feedback_metrics(self, client, db):
        _seed_cerebro_data(db)
        resp = client.get("/api/intel/cerebro-analytics")
        data = resp.json()
        assert "feedback_collected" in data
        assert data["feedback_collected"] == 1

    def test_returns_decisions_per_day(self, client, db):
        _seed_cerebro_data(db)
        resp = client.get("/api/intel/cerebro-analytics")
        data = resp.json()
        assert "decisions_per_day" in data
        assert isinstance(data["decisions_per_day"], list)
        assert len(data["decisions_per_day"]) > 0
        day = data["decisions_per_day"][0]
        assert "date" in day
        assert "count" in day

    def test_returns_accuracy_metrics(self, client, db):
        _seed_cerebro_data(db)
        resp = client.get("/api/intel/cerebro-analytics")
        data = resp.json()
        assert "accuracy" in data
        acc = data["accuracy"]
        assert "feedback_positive_rate" in acc
        assert acc["feedback_positive_rate"] == 100.0  # 1 positive out of 1

    def test_empty_database_returns_zeros(self, client, db):
        resp = client.get("/api/intel/cerebro-analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_decisions"] == 0
        assert data["decisions_per_day"] == []
        assert data["feedback_collected"] == 0

    def test_returns_farms_covered(self, client, db):
        _seed_cerebro_data(db)
        resp = client.get("/api/intel/cerebro-analytics")
        data = resp.json()
        assert "farms_covered" in data
        assert data["farms_covered"] == 1

    def test_returns_fields_analyzed(self, client, db):
        _seed_cerebro_data(db)
        resp = client.get("/api/intel/cerebro-analytics")
        data = resp.json()
        assert "fields_analyzed" in data
        assert data["fields_analyzed"] == 1
