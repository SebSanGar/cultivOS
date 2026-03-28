"""Tests for alert history widget — API data contract for the frontend timeline."""

from datetime import datetime

from cultivos.db.models import Alert, Farm, Field, HealthScore


def _seed_farm_with_alerts(db):
    """Create a farm with fields and various alert types."""
    farm = Farm(name="Rancho Alertas", state="Jalisco")
    db.add(farm)
    db.commit()
    db.refresh(farm)

    f1 = Field(farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=10.0)
    db.add(f1)
    db.commit()
    db.refresh(f1)

    # Three alerts of different types
    db.add(Alert(
        farm_id=farm.id, field_id=f1.id, alert_type="low_health",
        message="Salud baja en Parcela Norte: 35/100", phone_number=None,
        status="pending", sent_at=datetime(2026, 3, 10, 8, 0),
    ))
    db.add(Alert(
        farm_id=farm.id, field_id=f1.id, alert_type="irrigation",
        message="Riego urgente: Parcela Norte necesita 2500L/ha",
        phone_number="+521234567890", status="sent",
        sent_at=datetime(2026, 3, 12, 14, 30),
    ))
    db.add(Alert(
        farm_id=farm.id, field_id=f1.id, alert_type="anomaly_ndvi_drop",
        message="NDVI cayo 25% en Parcela Norte", phone_number=None,
        status="pending", sent_at=datetime(2026, 3, 15, 9, 0),
    ))
    db.commit()
    return farm


class TestAlertHistoryWidget:
    """Verify the alerts endpoint returns data the frontend timeline needs."""

    def test_alerts_list_returns_all_types(self, client, db, admin_headers):
        """GET /api/farms/{id}/alerts returns alerts with type, message, timestamp."""
        farm = _seed_farm_with_alerts(db)
        resp = client.get(f"/api/farms/{farm.id}/alerts", headers=admin_headers)

        assert resp.status_code == 200
        alerts = resp.json()
        assert len(alerts) == 3

        # Each alert has the fields the widget needs
        for alert in alerts:
            assert "alert_type" in alert
            assert "message" in alert
            assert "sent_at" in alert
            assert "status" in alert
            assert "field_id" in alert

    def test_alerts_ordered_most_recent_first(self, client, db, admin_headers):
        """Timeline shows newest alerts at the top."""
        farm = _seed_farm_with_alerts(db)
        resp = client.get(f"/api/farms/{farm.id}/alerts", headers=admin_headers)

        alerts = resp.json()
        dates = [a["sent_at"] for a in alerts]
        assert dates == sorted(dates, reverse=True)

    def test_alerts_include_all_known_types(self, client, db, admin_headers):
        """Widget receives the standard alert types it knows how to render."""
        farm = _seed_farm_with_alerts(db)
        resp = client.get(f"/api/farms/{farm.id}/alerts", headers=admin_headers)

        types = {a["alert_type"] for a in resp.json()}
        assert "low_health" in types
        assert "irrigation" in types
        assert "anomaly_ndvi_drop" in types

    def test_no_alerts_returns_empty_list(self, client, db, admin_headers):
        """Farm with no alerts returns empty list — widget shows empty state."""
        farm = Farm(name="Rancho Sin Alertas", state="Jalisco")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        resp = client.get(f"/api/farms/{farm.id}/alerts", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_alert_has_status_field(self, client, db, admin_headers):
        """Each alert includes status (pending/sent) for badge rendering."""
        farm = _seed_farm_with_alerts(db)
        resp = client.get(f"/api/farms/{farm.id}/alerts", headers=admin_headers)

        statuses = {a["status"] for a in resp.json()}
        assert "pending" in statuses
        assert "sent" in statuses

    def test_nonexistent_farm_returns_404(self, client, admin_headers):
        """Alert history for missing farm returns 404."""
        resp = client.get("/api/farms/9999/alerts", headers=admin_headers)
        assert resp.status_code == 404
