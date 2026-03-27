"""Tests for irrigation SMS alerts — water schedule notifications."""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import (
    Alert, Farm, Field, SoilAnalysis, ThermalResult, WeatherRecord,
)
from cultivos.services.alerts.sms import (
    format_irrigation_sms,
    should_send_alert,
)


class TestIrrigationAlertTriggered:
    """Irrigation urgency 'alta' triggers an SMS alert via the check endpoint."""

    def _seed_drought_field(self, client, admin_headers, db):
        """Create farm + field + thermal deficit data (urgency=alta)."""
        resp = client.post("/api/farms", json={
            "name": "Rancho Seco", "owner_name": "Don Manuel",
            "location_lat": 20.6, "location_lon": -103.3, "total_hectares": 40,
        }, headers=admin_headers)
        farm_id = resp.json()["id"]

        resp = client.post(f"/api/farms/{farm_id}/fields", json={
            "name": "Lote Norte", "crop_type": "maiz", "hectares": 10,
        }, headers=admin_headers)
        field_id = resp.json()["id"]

        # Thermal deficit → irrigation urgency "alta"
        thermal = ThermalResult(
            field_id=field_id,
            stress_pct=65.0,
            temp_mean=38.0,
            temp_std=3.5,
            temp_min=32.0,
            temp_max=44.0,
            pixels_total=10000,
            irrigation_deficit=True,
        )
        db.add(thermal)

        # Hot dry weather
        weather = WeatherRecord(
            farm_id=farm_id,
            temp_c=37.0,
            humidity_pct=25.0,
            wind_kmh=10.0,
            description="Despejado",
            forecast_3day=[],
        )
        db.add(weather)
        db.commit()

        return farm_id, field_id

    def test_irrigation_alert_triggered(self, client, admin_headers, db):
        """POST /alerts/check-irrigation creates alert when urgency is 'alta'."""
        farm_id, field_id = self._seed_drought_field(client, admin_headers, db)

        resp = client.post(
            f"/api/farms/{farm_id}/alerts/check-irrigation",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alerts_created"]) == 1
        alert = data["alerts_created"][0]
        assert alert["alert_type"] == "irrigation"
        assert alert["field_id"] == field_id

    def test_no_alert_for_low_urgency(self, client, admin_headers, db):
        """No alert created when irrigation urgency is 'baja'."""
        resp = client.post("/api/farms", json={
            "name": "Rancho Verde", "owner_name": "Maria",
            "location_lat": 20.6, "location_lon": -103.3, "total_hectares": 30,
        }, headers=admin_headers)
        farm_id = resp.json()["id"]

        resp = client.post(f"/api/farms/{farm_id}/fields", json={
            "name": "Parcela Sur", "crop_type": "frijol", "hectares": 5,
        }, headers=admin_headers)

        # No thermal stress, no extreme weather → urgency should be "baja"
        resp = client.post(
            f"/api/farms/{farm_id}/alerts/check-irrigation",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alerts_created"]) == 0


class TestAlertMessageSpanish:
    """Irrigation alert messages must be in Spanish with field name and liters/ha."""

    def test_alert_message_spanish(self):
        """format_irrigation_sms includes field name, liters/ha, urgency in Spanish."""
        msg = format_irrigation_sms(
            farm_name="Rancho Seco",
            field_name="Lote Norte",
            urgencia="alta",
            liters_per_ha=6500.0,
            crop_type="maiz",
        )
        # Must be in Spanish
        assert "Lote Norte" in msg
        assert "Rancho Seco" in msg
        assert "6500" in msg or "6,500" in msg
        # Spanish keywords
        assert "riego" in msg.lower() or "regar" in msg.lower()
        # No English
        assert "irrigation" not in msg.lower()
        assert "water" not in msg.lower()

    def test_critical_urgency_message(self):
        """Critical urgency includes action directive."""
        msg = format_irrigation_sms(
            farm_name="Rancho Seco",
            field_name="Lote Norte",
            urgencia="alta",
            liters_per_ha=7000.0,
            crop_type="maiz",
        )
        # Must tell farmer to ACT
        assert any(word in msg.lower() for word in ["regar", "riego", "urgente", "hoy", "inmediato"])

    def test_medium_urgency_message(self):
        """Medium urgency is less urgent but still in Spanish."""
        msg = format_irrigation_sms(
            farm_name="Rancho Verde",
            field_name="Parcela Sur",
            urgencia="media",
            liters_per_ha=4500.0,
            crop_type="frijol",
        )
        assert "Parcela Sur" in msg
        assert "4500" in msg or "4,500" in msg


class TestAlertDeduplication:
    """Same irrigation alert not sent twice in 24h."""

    def test_alert_deduplication(self, client, admin_headers, db):
        """Second check within 24h does not create duplicate irrigation alert."""
        resp = client.post("/api/farms", json={
            "name": "Rancho Doble", "owner_name": "Pedro",
            "location_lat": 20.6, "location_lon": -103.3, "total_hectares": 20,
        }, headers=admin_headers)
        farm_id = resp.json()["id"]

        resp = client.post(f"/api/farms/{farm_id}/fields", json={
            "name": "Parcela A", "crop_type": "maiz", "hectares": 5,
        }, headers=admin_headers)
        field_id = resp.json()["id"]

        # Thermal deficit → high urgency
        thermal = ThermalResult(
            field_id=field_id,
            stress_pct=60.0,
            temp_mean=36.0,
            temp_std=3.0,
            temp_min=30.0,
            temp_max=42.0,
            pixels_total=10000,
            irrigation_deficit=True,
        )
        db.add(thermal)

        weather = WeatherRecord(
            farm_id=farm_id,
            temp_c=36.0,
            humidity_pct=28.0,
            wind_kmh=8.0,
            description="Caluroso",
            forecast_3day=[],
        )
        db.add(weather)
        db.commit()

        # First check → creates alert
        resp1 = client.post(
            f"/api/farms/{farm_id}/alerts/check-irrigation",
            headers=admin_headers,
        )
        assert resp1.status_code == 200
        assert len(resp1.json()["alerts_created"]) == 1

        # Second check within 24h → no duplicate
        resp2 = client.post(
            f"/api/farms/{farm_id}/alerts/check-irrigation",
            headers=admin_headers,
        )
        assert resp2.status_code == 200
        assert len(resp2.json()["alerts_created"]) == 0
