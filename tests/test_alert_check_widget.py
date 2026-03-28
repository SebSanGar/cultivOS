"""Tests for alert check trigger — Verificar Alertas button on farm dashboard.

Verifies: POST /api/farms/{id}/alerts/check, check-irrigation, check-anomalies
return AlertCheckResponse with farm_id, alerts_created, fields_checked.
The frontend button triggers all 3 and renders color-coded result cards.
"""

from datetime import datetime, timedelta

from cultivos.db.models import (
    Farm, Field, HealthScore, NDVIResult, SoilAnalysis, WeatherRecord,
)


def _seed_farm_field(db):
    """Create a farm with one field for alert check tests."""
    farm = Farm(name="Rancho Verificar", state="Jalisco")
    db.add(farm)
    db.commit()
    db.refresh(farm)

    field = Field(farm_id=farm.id, name="Campo Alerta", crop_type="maiz", hectares=8.0)
    db.add(field)
    db.commit()
    db.refresh(field)
    return farm, field


def _seed_low_health(db, field, score=30):
    """Add a health score below the default threshold (40)."""
    hs = HealthScore(
        field_id=field.id, score=score,
        ndvi_mean=0.3, sources=["ndvi"],
        created_at=datetime.utcnow(),
    )
    db.add(hs)
    db.commit()


def _seed_anomaly_data(db, field):
    """Add two health scores with a >15-point drop to trigger anomaly."""
    now = datetime.utcnow()
    hs1 = HealthScore(
        field_id=field.id, score=80,
        ndvi_mean=0.7, sources=["ndvi"],
        created_at=now - timedelta(days=2),
    )
    hs2 = HealthScore(
        field_id=field.id, score=50,
        ndvi_mean=0.4, sources=["ndvi"],
        created_at=now,
    )
    db.add_all([hs1, hs2])
    db.commit()


class TestAlertCheckEndpoints:
    """Verify the three alert-check POST endpoints return AlertCheckResponse."""

    def test_check_health_creates_alert_for_low_score(self, client, db, admin_headers):
        """POST /api/farms/{id}/alerts/check creates alerts when health < threshold."""
        farm, field = _seed_farm_field(db)
        _seed_low_health(db, field, score=30)

        resp = client.post(f"/api/farms/{farm.id}/alerts/check", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()

        assert data["farm_id"] == farm.id
        assert data["fields_checked"] >= 1
        assert isinstance(data["alerts_created"], list)
        assert len(data["alerts_created"]) >= 1
        assert data["alerts_created"][0]["alert_type"] == "low_health"

    def test_check_health_no_alerts_when_healthy(self, client, db, admin_headers):
        """POST /api/farms/{id}/alerts/check creates no alerts when all fields are healthy."""
        farm, field = _seed_farm_field(db)
        _seed_low_health(db, field, score=85)

        resp = client.post(f"/api/farms/{farm.id}/alerts/check", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["alerts_created"] == []

    def test_check_irrigation_returns_response_shape(self, client, db, admin_headers):
        """POST /api/farms/{id}/alerts/check-irrigation returns AlertCheckResponse."""
        farm, field = _seed_farm_field(db)

        resp = client.post(
            f"/api/farms/{farm.id}/alerts/check-irrigation",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "farm_id" in data
        assert "alerts_created" in data
        assert "fields_checked" in data

    def test_check_anomalies_detects_health_drop(self, client, db, admin_headers):
        """POST /api/farms/{id}/alerts/check-anomalies detects >15pt health drop."""
        farm, field = _seed_farm_field(db)
        _seed_anomaly_data(db, field)

        resp = client.post(
            f"/api/farms/{farm.id}/alerts/check-anomalies",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["farm_id"] == farm.id
        assert data["fields_checked"] >= 1
        # Should detect the 80→50 drop (30 points > 15 threshold)
        anomaly_alerts = [a for a in data["alerts_created"]
                          if "anomaly" in a["alert_type"]]
        assert len(anomaly_alerts) >= 1

    def test_check_anomalies_no_alerts_when_stable(self, client, db, admin_headers):
        """POST /api/farms/{id}/alerts/check-anomalies: no alerts when no drops."""
        farm, field = _seed_farm_field(db)
        # Single health score — no drop to detect
        _seed_low_health(db, field, score=70)

        resp = client.post(
            f"/api/farms/{farm.id}/alerts/check-anomalies",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["alerts_created"] == []

    def test_all_three_checks_return_consistent_shape(self, client, db, admin_headers):
        """All three check endpoints return the same AlertCheckResponse shape."""
        farm, field = _seed_farm_field(db)

        endpoints = [
            f"/api/farms/{farm.id}/alerts/check",
            f"/api/farms/{farm.id}/alerts/check-irrigation",
            f"/api/farms/{farm.id}/alerts/check-anomalies",
        ]
        for endpoint in endpoints:
            resp = client.post(endpoint, headers=admin_headers)
            assert resp.status_code == 200, f"Failed: {endpoint}"
            data = resp.json()
            assert "farm_id" in data, f"Missing farm_id: {endpoint}"
            assert "alerts_created" in data, f"Missing alerts_created: {endpoint}"
            assert "fields_checked" in data, f"Missing fields_checked: {endpoint}"
