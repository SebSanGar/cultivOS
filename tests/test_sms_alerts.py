"""Tests for SMS alert service — send text notifications without WhatsApp dependency."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from cultivos.db.models import Alert, Farm, Field, HealthScore
from cultivos.services.alerts.sms import format_sms_message, should_send_alert


class TestFormatSmsMessage:
    """Pure function tests for SMS message formatting."""

    def test_send_sms(self):
        """Service formats SMS message with farm/field context."""
        msg = format_sms_message(
            farm_name="Rancho El Sol",
            field_name="Parcela Norte",
            alert_type="low_health",
            score=35.0,
        )
        assert isinstance(msg, str)
        assert len(msg) > 0
        assert "Rancho El Sol" in msg
        assert "Parcela Norte" in msg

    def test_alert_in_spanish(self):
        """SMS content is in Spanish."""
        msg = format_sms_message(
            farm_name="Rancho El Sol",
            field_name="Parcela Norte",
            alert_type="low_health",
            score=35.0,
        )
        # Should contain Spanish keywords, not English
        assert "salud" in msg.lower() or "alerta" in msg.lower()
        assert "health" not in msg.lower()


class TestShouldSendAlert:
    """Deduplication logic tests."""

    def test_no_duplicate_alerts(self, db):
        """Same alert not sent twice within 24 hours."""
        farm = Farm(name="Rancho Test", owner_name="Juan")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        field = Field(name="Parcela A", farm_id=farm.id, crop_type="maiz")
        db.add(field)
        db.commit()
        db.refresh(field)

        # Create a recent alert (within 24h)
        recent_alert = Alert(
            farm_id=farm.id,
            field_id=field.id,
            alert_type="low_health",
            message="Alerta previa",
            phone_number="+521234567890",
            sent_at=datetime.utcnow() - timedelta(hours=2),
        )
        db.add(recent_alert)
        db.commit()

        # Should NOT send duplicate
        result = should_send_alert(db, farm.id, field.id, "low_health")
        assert result is False

    def test_allows_alert_after_24h(self, db):
        """Alert can be sent if last one was >24h ago."""
        farm = Farm(name="Rancho Test", owner_name="Juan")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        field = Field(name="Parcela A", farm_id=farm.id, crop_type="maiz")
        db.add(field)
        db.commit()
        db.refresh(field)

        # Create an old alert (>24h)
        old_alert = Alert(
            farm_id=farm.id,
            field_id=field.id,
            alert_type="low_health",
            message="Alerta antigua",
            phone_number="+521234567890",
            sent_at=datetime.utcnow() - timedelta(hours=25),
        )
        db.add(old_alert)
        db.commit()

        # Should allow new alert
        result = should_send_alert(db, farm.id, field.id, "low_health")
        assert result is True


class TestAlertAPI:
    """API integration tests for alert endpoints."""

    def _seed_farm_field(self, client, admin_headers):
        resp = client.post("/api/farms", json={
            "name": "Rancho API", "owner_name": "Maria",
            "location_lat": 20.6, "location_lon": -103.3, "total_hectares": 50,
        }, headers=admin_headers)
        farm_id = resp.json()["id"]

        resp = client.post(f"/api/farms/{farm_id}/fields", json={
            "name": "Parcela Sur", "crop_type": "maiz", "hectares": 10,
        }, headers=admin_headers)
        field_id = resp.json()["id"]
        return farm_id, field_id

    def test_alert_on_low_health(self, client, admin_headers, db):
        """Health score <40 triggers alert creation via POST."""
        farm_id, field_id = self._seed_farm_field(client, admin_headers)

        # Create a low health score
        score = HealthScore(
            field_id=field_id, score=35.0, trend="declining",
            sources=["ndvi"], breakdown={"ndvi": 35.0},
        )
        db.add(score)
        db.commit()

        resp = client.post(
            f"/api/farms/{farm_id}/alerts/check",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alerts_created"]) > 0
        alert = data["alerts_created"][0]
        assert alert["alert_type"] == "low_health"
        assert "salud" in alert["message"].lower() or "alerta" in alert["message"].lower()

    def test_alert_history(self, client, admin_headers, db):
        """GET /api/farms/{id}/alerts returns chronological alert list."""
        farm_id, field_id = self._seed_farm_field(client, admin_headers)

        # Seed alerts directly
        for i in range(3):
            alert = Alert(
                farm_id=farm_id, field_id=field_id,
                alert_type="low_health",
                message=f"Alerta {i+1}",
                phone_number="+521234567890",
                sent_at=datetime.utcnow() - timedelta(days=3 - i),
            )
            db.add(alert)
        db.commit()

        resp = client.get(
            f"/api/farms/{farm_id}/alerts",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        # Most recent first
        assert data[0]["message"] == "Alerta 3"

    def test_no_alert_for_healthy_field(self, client, admin_headers, db):
        """Health score >=40 does NOT trigger alert."""
        farm_id, field_id = self._seed_farm_field(client, admin_headers)

        score = HealthScore(
            field_id=field_id, score=75.0, trend="stable",
            sources=["ndvi"], breakdown={"ndvi": 75.0},
        )
        db.add(score)
        db.commit()

        resp = client.post(
            f"/api/farms/{farm_id}/alerts/check",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alerts_created"]) == 0
