"""Tests for the alert history timeline page at /historial-alertas."""

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


def _seed_farm_with_alerts(db):
    """Seed a farm with fields, alerts and alert logs for testing."""
    farm = Farm(name="Rancho Prueba", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.commit()

    field = Field(farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=10.0)
    db.add(field)
    db.commit()

    now = datetime.utcnow()

    # SMS-type alerts
    a1 = Alert(
        farm_id=farm.id,
        field_id=field.id,
        alert_type="low_health",
        message="Salud baja en Parcela Norte: 35/100",
        status="sent",
        sent_at=now - timedelta(hours=2),
    )
    a2 = Alert(
        farm_id=farm.id,
        field_id=field.id,
        alert_type="irrigation",
        message="Riego urgente en Parcela Norte",
        status="pending",
        sent_at=now - timedelta(hours=1),
    )

    # System alert logs
    log1 = AlertLog(
        farm_id=farm.id,
        field_id=field.id,
        alert_type="anomaly_health_drop",
        message="Caida de salud detectada en Parcela Norte",
        severity="critical",
    )
    log2 = AlertLog(
        farm_id=farm.id,
        field_id=None,
        alert_type="weather",
        message="Alerta de sequia para Rancho Prueba",
        severity="warning",
    )

    db.add_all([a1, a2, log1, log2])
    db.commit()
    return farm, field


# ── Page Load Tests ────────────────────────────────────────────


class TestHistorialAlertasPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/historial-alertas")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/historial-alertas")
        assert "Historial de Alertas" in resp.text

    def test_page_has_subtitle(self, client):
        resp = client.get("/historial-alertas")
        text = resp.text.lower()
        assert "cronol" in text or "alertas generadas" in text

    def test_page_has_nav(self, client):
        resp = client.get("/historial-alertas")
        assert "<nav" in resp.text

    def test_page_has_styles_link(self, client):
        resp = client.get("/historial-alertas")
        assert "styles.css" in resp.text

    def test_page_has_js_link(self, client):
        resp = client.get("/historial-alertas")
        assert "historial-alertas.js" in resp.text


# ── Timeline Container ────────────────────────────────────────


class TestHistorialAlertasTimeline:
    """Timeline container and alert cards exist."""

    def test_has_timeline_container(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="alertas-timeline"' in resp.text

    def test_has_loading_state(self, client):
        resp = client.get("/historial-alertas")
        assert "Cargando" in resp.text or 'id="alertas-loading"' in resp.text


# ── Filter Controls ────────────────────────────────────────


class TestHistorialAlertasFilters:
    """Filter dropdowns for farm, type, severity, date range."""

    def test_has_farm_filter(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="alertas-farm-filter"' in resp.text

    def test_has_type_filter(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="alertas-type-filter"' in resp.text

    def test_has_severity_filter(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="alertas-severity-filter"' in resp.text

    def test_has_date_start(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="alertas-date-start"' in resp.text

    def test_has_date_end(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="alertas-date-end"' in resp.text


# ── Stats Strip ────────────────────────────────────────


class TestHistorialAlertasStats:
    """Stats strip with total alerts, critical count, pending count."""

    def test_has_stat_total(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="alertas-stat-total"' in resp.text

    def test_has_stat_critical(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="alertas-stat-critical"' in resp.text

    def test_has_stat_pending(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="alertas-stat-pending"' in resp.text

    def test_has_stat_farms(self, client):
        resp = client.get("/historial-alertas")
        assert 'id="alertas-stat-farms"' in resp.text


# ── API Endpoint Tests ────────────────────────────────────────


class TestAlertHistoryAPI:
    """GET /api/alerts/history returns combined alert data."""

    def test_returns_200(self, client):
        resp = client.get("/api/alerts/history")
        assert resp.status_code == 200

    def test_returns_list(self, client):
        resp = client.get("/api/alerts/history")
        data = resp.json()
        assert isinstance(data, list)

    def test_returns_seeded_alerts(self, client, db):
        _seed_farm_with_alerts(db)
        resp = client.get("/api/alerts/history")
        data = resp.json()
        assert len(data) == 4  # 2 Alert + 2 AlertLog

    def test_alert_has_required_fields(self, client, db):
        _seed_farm_with_alerts(db)
        resp = client.get("/api/alerts/history")
        data = resp.json()
        entry = data[0]
        required = ["id", "farm_id", "alert_type", "message", "severity", "source", "created_at"]
        for field in required:
            assert field in entry, f"Missing field: {field}"

    def test_source_distinguishes_sms_and_system(self, client, db):
        _seed_farm_with_alerts(db)
        resp = client.get("/api/alerts/history")
        data = resp.json()
        sources = {e["source"] for e in data}
        assert "sms" in sources
        assert "system" in sources

    def test_filter_by_farm_id(self, client, db):
        farm, _ = _seed_farm_with_alerts(db)
        resp = client.get(f"/api/alerts/history?farm_id={farm.id}")
        data = resp.json()
        assert len(data) == 4
        assert all(e["farm_id"] == farm.id for e in data)

    def test_filter_by_nonexistent_farm(self, client, db):
        _seed_farm_with_alerts(db)
        resp = client.get("/api/alerts/history?farm_id=9999")
        data = resp.json()
        assert len(data) == 0

    def test_filter_by_alert_type(self, client, db):
        _seed_farm_with_alerts(db)
        resp = client.get("/api/alerts/history?alert_type=irrigation")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["alert_type"] == "irrigation"

    def test_filter_by_severity(self, client, db):
        _seed_farm_with_alerts(db)
        resp = client.get("/api/alerts/history?severity=critical")
        data = resp.json()
        # low_health (sms, mapped to critical) + anomaly_health_drop (system, critical)
        assert len(data) == 2
        assert all(e["severity"] == "critical" for e in data)

    def test_results_ordered_newest_first(self, client, db):
        _seed_farm_with_alerts(db)
        resp = client.get("/api/alerts/history")
        data = resp.json()
        dates = [e["created_at"] for e in data]
        assert dates == sorted(dates, reverse=True)

    def test_sms_alert_includes_status(self, client, db):
        _seed_farm_with_alerts(db)
        resp = client.get("/api/alerts/history")
        data = resp.json()
        sms_entries = [e for e in data if e["source"] == "sms"]
        for entry in sms_entries:
            assert "status" in entry

    def test_system_alert_includes_acknowledged(self, client, db):
        _seed_farm_with_alerts(db)
        resp = client.get("/api/alerts/history")
        data = resp.json()
        sys_entries = [e for e in data if e["source"] == "system"]
        for entry in sys_entries:
            assert "acknowledged" in entry
