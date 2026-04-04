"""Tests for GET /api/alerts/analytics — delivery metrics and farmer engagement KPIs."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Alert, AlertLog, Farm, Field
from cultivos.db.session import get_db


@pytest.fixture()
def app(db):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def _seed_alerts(db):
    """Seed realistic alert data for analytics testing."""
    farm = Farm(name="Rancho Analisis", state="Jalisco", total_hectares=80.0)
    db.add(farm)
    db.commit()

    f1 = Field(farm_id=farm.id, name="Parcela A", crop_type="maiz", hectares=20.0)
    f2 = Field(farm_id=farm.id, name="Parcela B", crop_type="agave", hectares=30.0)
    db.add_all([f1, f2])
    db.commit()

    now = datetime.utcnow()

    alerts = [
        Alert(farm_id=farm.id, field_id=f1.id, alert_type="low_health",
              message="Salud baja en A", status="sent",
              sent_at=now - timedelta(hours=5)),
        Alert(farm_id=farm.id, field_id=f1.id, alert_type="low_health",
              message="Salud baja en A otra vez", status="sent",
              sent_at=now - timedelta(hours=3)),
        Alert(farm_id=farm.id, field_id=f2.id, alert_type="irrigation",
              message="Riego urgente B", status="pending",
              sent_at=now - timedelta(hours=1)),
        Alert(farm_id=farm.id, field_id=f2.id, alert_type="irrigation",
              message="Riego urgente B2", status="failed",
              sent_at=now - timedelta(hours=2)),
        Alert(farm_id=farm.id, field_id=f1.id, alert_type="anomaly_health_drop",
              message="Anomalia en A", status="sent",
              sent_at=now - timedelta(days=2)),
    ]

    logs = [
        AlertLog(farm_id=farm.id, field_id=f1.id, alert_type="health",
                 message="Salud check A", severity="warning", acknowledged=True),
        AlertLog(farm_id=farm.id, field_id=f2.id, alert_type="recommendation",
                 message="Recomendacion B", severity="info", acknowledged=False),
    ]

    db.add_all(alerts + logs)
    db.commit()
    return farm


def _seed_two_farms(db):
    """Seed two farms for multi-farm analytics."""
    farm1 = Farm(name="Rancho Uno", state="Jalisco", total_hectares=40.0)
    farm2 = Farm(name="Rancho Dos", state="Michoacan", total_hectares=60.0)
    db.add_all([farm1, farm2])
    db.commit()

    f1 = Field(farm_id=farm1.id, name="Campo 1", crop_type="maiz", hectares=10.0)
    f2 = Field(farm_id=farm2.id, name="Campo 2", crop_type="agave", hectares=20.0)
    db.add_all([f1, f2])
    db.commit()

    now = datetime.utcnow()
    alerts = [
        Alert(farm_id=farm1.id, field_id=f1.id, alert_type="low_health",
              message="Baja salud", status="sent", sent_at=now),
        Alert(farm_id=farm2.id, field_id=f2.id, alert_type="irrigation",
              message="Riego", status="pending", sent_at=now),
        Alert(farm_id=farm2.id, field_id=f2.id, alert_type="low_health",
              message="Baja salud 2", status="sent", sent_at=now),
    ]
    db.add_all(alerts)
    db.commit()
    return farm1, farm2


# ── Endpoint Structure ────────────────────────────────────────


class TestAnalyticsEndpointStructure:
    """GET /api/alerts/analytics returns expected shape."""

    def test_returns_200(self, client):
        resp = client.get("/api/alerts/analytics")
        assert resp.status_code == 200

    def test_returns_dict(self, client):
        resp = client.get("/api/alerts/analytics")
        data = resp.json()
        assert isinstance(data, dict)

    def test_has_required_top_level_keys(self, client):
        resp = client.get("/api/alerts/analytics")
        data = resp.json()
        required = ["total_alerts", "total_sms", "total_system",
                     "delivery_rate", "by_type", "by_severity",
                     "by_status", "farms_reached", "fields_reached"]
        for key in required:
            assert key in data, f"Missing key: {key}"


# ── Empty State ────────────────────────────────────────


class TestAnalyticsEmptyState:
    """Analytics with no alerts returns zero-value defaults."""

    def test_total_alerts_zero(self, client):
        data = client.get("/api/alerts/analytics").json()
        assert data["total_alerts"] == 0

    def test_delivery_rate_zero(self, client):
        data = client.get("/api/alerts/analytics").json()
        assert data["delivery_rate"] == 0.0

    def test_by_type_empty(self, client):
        data = client.get("/api/alerts/analytics").json()
        assert data["by_type"] == {}

    def test_farms_reached_zero(self, client):
        data = client.get("/api/alerts/analytics").json()
        assert data["farms_reached"] == 0


# ── Aggregated Counts ────────────────────────────────────────


class TestAnalyticsCounts:
    """Correct counts from seeded alert data."""

    def test_total_alerts(self, client, db):
        _seed_alerts(db)
        data = client.get("/api/alerts/analytics").json()
        assert data["total_alerts"] == 7  # 5 SMS + 2 system

    def test_total_sms(self, client, db):
        _seed_alerts(db)
        data = client.get("/api/alerts/analytics").json()
        assert data["total_sms"] == 5

    def test_total_system(self, client, db):
        _seed_alerts(db)
        data = client.get("/api/alerts/analytics").json()
        assert data["total_system"] == 2

    def test_by_type_breakdown(self, client, db):
        _seed_alerts(db)
        data = client.get("/api/alerts/analytics").json()
        by_type = data["by_type"]
        assert by_type["low_health"] == 2
        assert by_type["irrigation"] == 2
        assert by_type["anomaly_health_drop"] == 1
        assert by_type["health"] == 1
        assert by_type["recommendation"] == 1

    def test_by_severity_breakdown(self, client, db):
        _seed_alerts(db)
        data = client.get("/api/alerts/analytics").json()
        by_sev = data["by_severity"]
        # SMS: low_health x2 → critical, irrigation x2 → warning, anomaly_health_drop → critical
        # System: health → warning, recommendation → info
        assert by_sev["critical"] == 3  # 2 low_health + 1 anomaly_health_drop
        assert by_sev["warning"] == 3  # 2 irrigation + 1 health
        assert by_sev["info"] == 1  # 1 recommendation

    def test_by_status_breakdown(self, client, db):
        _seed_alerts(db)
        data = client.get("/api/alerts/analytics").json()
        by_status = data["by_status"]
        assert by_status["sent"] == 3
        assert by_status["pending"] == 1
        assert by_status["failed"] == 1


# ── Delivery Rate ────────────────────────────────────────


class TestAnalyticsDeliveryRate:
    """Delivery rate = sent / total SMS alerts."""

    def test_delivery_rate_with_data(self, client, db):
        _seed_alerts(db)
        data = client.get("/api/alerts/analytics").json()
        # 3 sent out of 5 SMS alerts = 60%
        assert data["delivery_rate"] == pytest.approx(60.0, abs=0.1)


# ── Reach Metrics ────────────────────────────────────────


class TestAnalyticsReach:
    """Farms and fields reached by alerts."""

    def test_farms_reached(self, client, db):
        _seed_alerts(db)
        data = client.get("/api/alerts/analytics").json()
        assert data["farms_reached"] == 1

    def test_fields_reached(self, client, db):
        _seed_alerts(db)
        data = client.get("/api/alerts/analytics").json()
        assert data["fields_reached"] == 2

    def test_multi_farm_reach(self, client, db):
        _seed_two_farms(db)
        data = client.get("/api/alerts/analytics").json()
        assert data["farms_reached"] == 2
        assert data["fields_reached"] == 2


# ── Farm Filter ────────────────────────────────────────


class TestAnalyticsFarmFilter:
    """Analytics can be filtered by farm_id."""

    def test_filter_by_farm(self, client, db):
        farm1, farm2 = _seed_two_farms(db)
        data = client.get(f"/api/alerts/analytics?farm_id={farm1.id}").json()
        assert data["total_alerts"] == 1
        assert data["farms_reached"] == 1

    def test_filter_nonexistent_farm(self, client, db):
        _seed_alerts(db)
        data = client.get("/api/alerts/analytics?farm_id=9999").json()
        assert data["total_alerts"] == 0


# ── Frontend Analytics Section ────────────────────────────────


class TestHistorialAlertasAnalyticsSection:
    """The /historial-alertas page has an analytics KPI section."""

    def test_has_analytics_section(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="alertas-analytics"' in resp.text

    def test_has_delivery_rate_stat(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="analytics-delivery-rate"' in resp.text

    def test_has_sms_count_stat(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="analytics-sms-count"' in resp.text

    def test_has_system_count_stat(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="analytics-system-count"' in resp.text

    def test_has_farms_reached_stat(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="analytics-farms-reached"' in resp.text

    def test_has_analytics_title(self, client):
        resp = client.get("/historial-alertas")
        text = resp.text.lower()
        assert "anali" in text or "metricas" in text or "engagement" in text
