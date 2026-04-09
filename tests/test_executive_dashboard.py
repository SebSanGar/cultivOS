"""Tests for multi-farm executive dashboard at /ejecutivo."""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import (
    Alert,
    AlertLog,
    Farm,
    FarmerFeedback,
    Field,
    HealthScore,
    SoilAnalysis,
    TreatmentRecord,
)


def _seed_executive_data(db):
    """Seed 2 farms with fields, health scores, treatments, alerts, and soil data."""
    now = datetime.utcnow()

    farm1 = Farm(name="Rancho Sol", state="Jalisco", total_hectares=60.0)
    farm2 = Farm(name="Rancho Luna", state="Jalisco", total_hectares=40.0)
    db.add_all([farm1, farm2])
    db.flush()

    f1 = Field(farm_id=farm1.id, name="Maiz Norte", hectares=30.0, crop_type="maiz")
    f2 = Field(farm_id=farm1.id, name="Agave Sur", hectares=30.0, crop_type="agave")
    f3 = Field(farm_id=farm2.id, name="Frijol", hectares=40.0, crop_type="frijol")
    db.add_all([f1, f2, f3])
    db.flush()

    # Health scores
    db.add(HealthScore(field_id=f1.id, score=70.0, sources=["ndvi"], breakdown={}, scored_at=now - timedelta(days=5)))
    db.add(HealthScore(field_id=f2.id, score=80.0, sources=["ndvi"], breakdown={}, scored_at=now - timedelta(days=3)))
    db.add(HealthScore(field_id=f3.id, score=60.0, sources=["ndvi"], breakdown={}, scored_at=now - timedelta(days=1)))

    # Treatments
    for _ in range(3):
        db.add(TreatmentRecord(
            field_id=f1.id, health_score_used=70.0,
            problema="p", causa_probable="c", tratamiento="t",
            urgencia="media", prevencion="p",
        ))
    for _ in range(2):
        db.add(TreatmentRecord(
            field_id=f3.id, health_score_used=60.0,
            problema="p", causa_probable="c", tratamiento="t",
            urgencia="alta", prevencion="p",
        ))

    # Soil for carbon estimation
    db.add(SoilAnalysis(
        field_id=f1.id, ph=6.5, organic_matter_pct=3.5, nitrogen_ppm=40,
        phosphorus_ppm=20, potassium_ppm=150, sampled_at=now - timedelta(days=10),
    ))
    db.add(SoilAnalysis(
        field_id=f3.id, ph=6.8, organic_matter_pct=4.0, nitrogen_ppm=45,
        phosphorus_ppm=25, potassium_ppm=160, sampled_at=now - timedelta(days=7),
    ))

    # Alert logs (last 30 days)
    db.add(AlertLog(farm_id=farm1.id, field_id=f1.id, alert_type="health", message="Low health", severity="warning"))
    db.add(AlertLog(farm_id=farm2.id, field_id=f3.id, alert_type="irrigation", message="Needs water", severity="critical"))
    db.add(AlertLog(farm_id=farm1.id, field_id=f2.id, alert_type="pest", message="Pest risk", severity="info"))

    db.commit()
    return farm1, farm2


# ── Service tests ────────────────────────────────────────────


class TestComputeExecutiveSummary:
    def test_aggregates_platform_kpis(self, db):
        _seed_executive_data(db)
        from cultivos.services.intelligence.analytics import compute_executive_summary
        result = compute_executive_summary(db)

        assert result["total_farms"] == 2
        assert result["total_fields"] == 3
        assert result["total_hectares"] == 100.0
        assert result["avg_health"] is not None
        # Avg of latest scores: (70 + 80 + 60) / 3 = 70.0
        assert abs(result["avg_health"] - 70.0) < 0.1
        assert result["total_treatments"] == 5
        assert result["active_alerts"] == 3

    def test_co2e_sequestration(self, db):
        _seed_executive_data(db)
        from cultivos.services.intelligence.analytics import compute_executive_summary
        result = compute_executive_summary(db)
        # Should have some CO2e value from soil data
        assert result["total_co2e_tonnes"] >= 0

    def test_empty_platform(self, db):
        from cultivos.services.intelligence.analytics import compute_executive_summary
        result = compute_executive_summary(db)
        assert result["total_farms"] == 0
        assert result["total_fields"] == 0
        assert result["total_hectares"] == 0
        assert result["avg_health"] is None
        assert result["total_treatments"] == 0
        assert result["active_alerts"] == 0
        assert result["total_co2e_tonnes"] == 0

    def test_activity_30d_list(self, db):
        _seed_executive_data(db)
        from cultivos.services.intelligence.analytics import compute_executive_summary
        result = compute_executive_summary(db)
        # Should have a list of daily activity counts
        assert "activity_30d" in result
        assert isinstance(result["activity_30d"], list)

    def test_farms_breakdown(self, db):
        _seed_executive_data(db)
        from cultivos.services.intelligence.analytics import compute_executive_summary
        result = compute_executive_summary(db)
        assert "farms" in result
        assert len(result["farms"]) == 2
        for f in result["farms"]:
            assert "farm_id" in f
            assert "farm_name" in f
            assert "field_count" in f
            assert "avg_health" in f


# ── API endpoint tests ──────────────────────────────────────


class TestExecutiveSummaryEndpoint:
    def test_returns_200(self, client, db):
        _seed_executive_data(db)
        resp = client.get("/api/intel/executive-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_farms"] == 2
        assert data["total_fields"] == 3

    def test_empty_state(self, client, db):
        resp = client.get("/api/intel/executive-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_farms"] == 0

    def test_response_schema(self, client, db):
        _seed_executive_data(db)
        resp = client.get("/api/intel/executive-summary")
        data = resp.json()
        required = {
            "total_farms", "total_fields", "total_hectares", "avg_health",
            "total_treatments", "active_alerts", "total_co2e_tonnes",
            "activity_30d", "farms",
        }
        assert required.issubset(data.keys())


# ── Frontend page tests ─────────────────────────────────────


class TestEjecutivoPage:
    def test_page_loads(self, client):
        resp = client.get("/ejecutivo")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_page_has_spanish_title(self, client):
        resp = client.get("/ejecutivo")
        assert "Ejecutivo" in resp.text or "ejecutivo" in resp.text.lower()

    def test_page_has_stats_containers(self, client):
        resp = client.get("/ejecutivo")
        text = resp.text
        assert "exec-farms" in text or "total-farms" in text

    def test_page_has_activity_chart(self, client):
        resp = client.get("/ejecutivo")
        assert "activity-chart" in resp.text or "activityChart" in resp.text

    def test_page_has_farms_table(self, client):
        resp = client.get("/ejecutivo")
        assert "farms-table" in resp.text or "farmsTable" in resp.text

    def test_page_references_js(self, client):
        resp = client.get("/ejecutivo")
        assert "ejecutivo.js" in resp.text

    def test_js_file_loads(self, client):
        resp = client.get("/ejecutivo.js")
        assert resp.status_code == 200
