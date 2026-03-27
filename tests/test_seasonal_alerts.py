"""Tests for seasonal TEK calendar alerts."""

from datetime import date

import pytest

from cultivos.services.intelligence.seasonal_calendar import generate_seasonal_alerts


class TestSeasonalAlertsTemporal:
    """Correct alert for temporal season crops."""

    def test_temporal_prep_window_march(self):
        """March should trigger prep alerts for temporal crops (maiz, frijol, calabaza)."""
        alerts = generate_seasonal_alerts(reference_date=date(2026, 3, 15))
        crop_names = [a["crop"] for a in alerts]
        assert "Maiz" in crop_names
        assert "Frijol" in crop_names
        assert "Calabaza" in crop_names
        # All should be prep-type alerts
        prep_alerts = [a for a in alerts if a["alert_type"] == "preparacion"]
        assert len(prep_alerts) >= 3

    def test_temporal_planting_window_june(self):
        """June should trigger planting alerts for temporal crops."""
        alerts = generate_seasonal_alerts(reference_date=date(2026, 6, 10))
        planting = [a for a in alerts if a["alert_type"] == "siembra"]
        crop_names = [a["crop"] for a in planting]
        assert "Maiz" in crop_names
        assert "Frijol" in crop_names

    def test_secas_planting_window_november(self):
        """November should trigger planting alerts for secas crops (garbanzo)."""
        alerts = generate_seasonal_alerts(reference_date=date(2026, 11, 15))
        planting = [a for a in alerts if a["alert_type"] == "siembra"]
        crop_names = [a["crop"] for a in planting]
        assert "Garbanzo" in crop_names


class TestMilpaWindow:
    """Milpa window matches March-April."""

    def test_milpa_alert_in_march(self):
        """March should generate a milpa-specific alert."""
        alerts = generate_seasonal_alerts(reference_date=date(2026, 3, 20))
        milpa = [a for a in alerts if a["crop"] == "Milpa"]
        assert len(milpa) == 1
        assert "milpa" in milpa[0]["message"].lower()

    def test_milpa_alert_in_april(self):
        """April should also generate a milpa-specific alert."""
        alerts = generate_seasonal_alerts(reference_date=date(2026, 4, 10))
        milpa = [a for a in alerts if a["crop"] == "Milpa"]
        assert len(milpa) == 1

    def test_no_milpa_alert_in_august(self):
        """August is outside milpa prep window — no milpa alert."""
        alerts = generate_seasonal_alerts(reference_date=date(2026, 8, 15))
        milpa = [a for a in alerts if a["crop"] == "Milpa"]
        assert len(milpa) == 0


class TestNoAlertOutsideWindow:
    """No alert when outside window."""

    def test_no_temporal_prep_in_july(self):
        """July is growing season — no prep alerts for temporal crops."""
        alerts = generate_seasonal_alerts(reference_date=date(2026, 7, 15))
        prep = [a for a in alerts if a["alert_type"] == "preparacion"]
        temporal_prep = [a for a in prep if a["crop"] in ("Maiz", "Frijol", "Calabaza")]
        assert len(temporal_prep) == 0

    def test_no_garbanzo_planting_in_march(self):
        """March is not planting time for garbanzo."""
        alerts = generate_seasonal_alerts(reference_date=date(2026, 3, 15))
        garbanzo_planting = [
            a for a in alerts
            if a["crop"] == "Garbanzo" and a["alert_type"] == "siembra"
        ]
        assert len(garbanzo_planting) == 0


class TestAlertTextInSpanish:
    """Alert text in Spanish."""

    def test_message_is_spanish(self):
        """All alert messages should be in Spanish."""
        alerts = generate_seasonal_alerts(reference_date=date(2026, 3, 15))
        assert len(alerts) > 0
        for alert in alerts:
            assert isinstance(alert["message"], str)
            assert len(alert["message"]) > 10
            # Should not contain English keywords
            msg_lower = alert["message"].lower()
            assert "plant" not in msg_lower or "planta" in msg_lower
            assert "harvest" not in msg_lower

    def test_alert_has_required_fields(self):
        """Each alert must have crop, alert_type, message, season, month_range."""
        alerts = generate_seasonal_alerts(reference_date=date(2026, 3, 15))
        for alert in alerts:
            assert "crop" in alert
            assert "alert_type" in alert
            assert "message" in alert
            assert "season" in alert
            assert "month_range" in alert


class TestAPIEndpoint:
    """Test the REST API endpoint."""

    def test_seasonal_alerts_endpoint(self, client, db, admin_headers):
        """GET /api/farms/{id}/seasonal-alerts returns alerts."""
        from cultivos.db.models import Farm
        farm = Farm(name="Test Farm", state="Jalisco")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        resp = client.get(
            f"/api/farms/{farm.id}/seasonal-alerts",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "alerts" in data
        assert "season" in data
        assert isinstance(data["alerts"], list)

    def test_seasonal_alerts_farm_not_found(self, client, admin_headers):
        """Non-existent farm returns 404."""
        resp = client.get("/api/farms/9999/seasonal-alerts", headers=admin_headers)
        assert resp.status_code == 404
